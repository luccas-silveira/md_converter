"""
Rotas para processamento de reuniões e geração de resumos
"""

from flask import Blueprint, request, send_file, abort, jsonify, current_app
from pathlib import Path
import tempfile
import traceback
import logging
import uuid
from typing import Optional, List
import os
import threading

from app.utils.md_to_pdf import md_to_pdf
from app.routes.progress import update_progress
from app.utils.file_security import sanitize_filename
from config.env_loader import load_env_from_file

# Garantir que variáveis do .env estejam carregadas antes de acessar OpenAI
load_env_from_file()

from openai import OpenAI

meeting_bp = Blueprint('meeting', __name__)
logger = logging.getLogger(__name__)

# Get application root
APP_ROOT = Path(__file__).resolve().parent.parent.parent

# Configurar OpenAI API e modelo (carregados dinamicamente)
DEFAULT_MODEL = 'gpt-4o-mini'
_openai_client: Optional[OpenAI] = None
_openai_api_key_loaded: Optional[str] = None
_logged_missing_key = False
_openai_lock = threading.Lock()


def get_model_candidates() -> List[str]:
    """Retorna a lista de modelos a tentar, priorizando o configurado via ambiente."""
    preferred = os.getenv('OPENAI_MODEL')
    models: List[str] = []
    if preferred:
        models.append(preferred)
    if DEFAULT_MODEL not in models:
        models.append(DEFAULT_MODEL)
    return models


def get_openai_client() -> Optional[OpenAI]:
    """Obtém (ou cria) um cliente OpenAI baseado nas variáveis de ambiente atuais."""
    global _openai_client, _openai_api_key_loaded, _logged_missing_key

    with _openai_lock:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            if not _logged_missing_key:
                logger.warning("OPENAI_API_KEY não encontrada - usando modo de demonstração")
                _logged_missing_key = True
            _openai_client = None
            _openai_api_key_loaded = None
            return None

        _logged_missing_key = False

        if api_key != _openai_api_key_loaded:
            _openai_client = OpenAI(api_key=api_key)
            _openai_api_key_loaded = api_key
            logger.info(f"OpenAI API configurada. Modelo preferencial: {os.getenv('OPENAI_MODEL', DEFAULT_MODEL)}")

        return _openai_client

def transcribe_audio_cloud(file_path: Path, language: str = "pt") -> str:
    """
    Transcreve áudio usando Whisper Cloud API da OpenAI.

    Vantagens sobre Whisper local:
    - Sem necessidade de carregar modelo (~350MB RAM)
    - Transcrição mais rápida (processamento distribuído)
    - Suporte a arquivos maiores (até 25MB)
    - Menor complexidade de deploy

    Args:
        file_path: Caminho do arquivo de áudio
        language: Código do idioma (padrão: 'pt' para português)

    Returns:
        Texto transcrito

    Raises:
        ValueError: Arquivo muito grande (>25MB)
        Exception: Erro na API OpenAI
    """
    logger.info(f"[Whisper Cloud] Transcrevendo áudio: {file_path.name}")

    client = get_openai_client()
    if not client:
        raise RuntimeError("OpenAI API não configurada")

    # Validar tamanho do arquivo (limite da API: 25MB)
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 25:
        raise ValueError(f"Arquivo muito grande ({file_size_mb:.1f}MB). Limite: 25MB")

    try:
        with open(file_path, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",  # Modelo universal da API
                file=audio_file,
                language=language,
                response_format="text"
            )

        transcript = response if isinstance(response, str) else response
        logger.info(f"[Whisper Cloud] Transcrição concluída: {len(transcript)} caracteres")
        return transcript

    except Exception as e:
        logger.error(f"[Whisper Cloud] Erro na transcrição: {e}")
        raise


@meeting_bp.route("/process-meeting", methods=["POST"])
def process_meeting():
    session_id = request.form.get('session_id', str(uuid.uuid4()))
    try:
        logger.info("=== INICIO DO PROCESSAMENTO DE REUNIÃO ===")
        update_progress(session_id, 5, "Iniciando processamento...")

        meeting_file = request.files.get("meeting_file")
        if not meeting_file:
            logger.error("Nenhum arquivo de reunião enviado")
            abort(400, "Nenhum arquivo de reunião enviado")

        # Sanitizar nome do arquivo para prevenir path traversal
        try:
            filename = sanitize_filename(
                meeting_file.filename,
                default_extension='.txt',  # Default para reuniões
                max_length=200
            )
        except ValueError as e:
            logger.error(f"Erro ao sanitizar filename: {e}")
            abort(400, "Nome de arquivo inválido")

        logger.info(f"Arquivo de reunião recebido (sanitizado): {filename}")
        logger.info(f"Tipo de conteúdo: {meeting_file.content_type}")

        # Meeting metadata
        participants = request.form.get('meeting_participants', '')
        meeting_date = request.form.get('meeting_date', '')
        meeting_title = request.form.get('meeting_title', '') or 'Resumo de Reunião'

        logger.info(f"Participantes: {participants}")
        logger.info(f"Data: {meeting_date}")
        logger.info(f"Título: {meeting_title}")

        # Cover data from form
        cover_data = {
            'topo_direito_email': request.form.get('cover_top_email', ''),
            'topo_direito_site': request.form.get('cover_top_site', ''),
            'representante_label': request.form.get('cover_rep_label', ''),
            'representante_nome': request.form.get('cover_rep_nome', ''),
            'subtitulo': meeting_title,
            'descricao': f"Reunião realizada em {meeting_date}" if meeting_date else "Resumo de reunião",
            'preparado_nome': request.form.get('cover_prep_nome', ''),
            'preparado_email': request.form.get('cover_prep_email', ''),
            'preparado_phone': request.form.get('cover_prep_phone', ''),
            'data': meeting_date or request.form.get('cover_data', ''),
        }

        upload_base = current_app.config.get('UPLOAD_FOLDER', '/tmp')
        with tempfile.TemporaryDirectory(dir=upload_base) as tmpdir:
            tmpdir_path = Path(tmpdir)
            logger.info(f"Diretório temporário: {tmpdir_path}")

            # Save uploaded meeting file
            meeting_path = tmpdir_path / filename
            meeting_file.save(meeting_path)
            logger.info(f"Arquivo de reunião salvo em: {meeting_path}")

            # Process the meeting file and generate markdown summary
            update_progress(session_id, 15, "Processando arquivo de reunião...")
            summary_md = process_meeting_file(meeting_path, participants, meeting_date, meeting_title, session_id)

            # Save summary as markdown file
            md_path = tmpdir_path / "resumo_reuniao.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(summary_md)
            logger.info(f"Resumo em markdown salvo em: {md_path}")

            # Generate PDF from markdown
            pdf_out = tmpdir_path / "resumo_reuniao.pdf"
            logger.info("Convertendo resumo para PDF")
            update_progress(session_id, 80, "Gerando PDF...")

            md_to_pdf(
                str(md_path),
                str(pdf_out),
                css_style=None,
                logo_path=None,
                base_dir=str(APP_ROOT),
                cover_data=cover_data,
                cover_template_path=None,
            )

            logger.info("Conversão para PDF concluída")
            update_progress(session_id, 95, "Finalizando...")

            if not pdf_out.exists():
                raise Exception(f"PDF não foi criado em {pdf_out}")

            logger.info(f"Tamanho do PDF: {pdf_out.stat().st_size} bytes")
            update_progress(session_id, 100, "Concluído!")

            return send_file(
                pdf_out,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=sanitize_filename(meeting_title + '.pdf', default_extension='.pdf', max_length=200),
            )

    except Exception as e:
        logger.error(f"ERRO DURANTE PROCESSAMENTO DE REUNIÃO: {str(e)}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return jsonify({
            "error": "Erro interno durante o processamento de reunião"
        }), 500


def process_meeting_file(file_path: Path, participants: str, meeting_date: str, meeting_title: str, session_id: str) -> str:
    """
    Process meeting file and generate markdown summary using AI.
    """
    logger.info(f"Processando arquivo de reunião: {file_path}")

    # Extract file extension to determine file type
    file_ext = file_path.suffix.lower()

    transcript = ""

    if file_ext in ['.txt', '.md']:
        # Text file - read directly (limit to 10MB to prevent OOM)
        max_text_size = 10 * 1024 * 1024  # 10MB
        file_size = file_path.stat().st_size
        if file_size > max_text_size:
            raise ValueError(f"Arquivo de texto muito grande ({file_size / (1024*1024):.1f}MB). Limite: 10MB")
        update_progress(session_id, 25, "Lendo arquivo de texto...")
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        logger.info("Arquivo de texto lido diretamente")

    elif file_ext in ['.mp3', '.wav', '.mp4', '.avi', '.mov', '.m4a']:
        # Audio/Video file - use Whisper Cloud API
        try:
            update_progress(session_id, 25, "Transcrevendo áudio com Whisper Cloud...")
            logger.info("Iniciando transcrição com Whisper Cloud API...")

            # Transcrever usando Whisper Cloud API
            transcript = transcribe_audio_cloud(file_path, language="pt")

            logger.info(f"Transcrição concluída. Tamanho: {len(transcript)} caracteres")
            update_progress(session_id, 50, "Transcrição concluída")
        except ValueError as e:
            # Arquivo muito grande
            logger.error(f"Arquivo muito grande para Whisper Cloud: {e}")
            transcript = f"[ERRO: ARQUIVO MUITO GRANDE]\n\nArquivo: {file_path.name}\n{str(e)}\n\nO limite da API Whisper é 25MB. Por favor, use um arquivo menor ou divida o áudio."
        except Exception as e:
            logger.error(f"Erro na transcrição Whisper Cloud: {e}")
            transcript = f"[ERRO NA TRANSCRIÇÃO]\n\nArquivo: {file_path.name}\nErro: {str(e)}\n\nVerifique se a API Key OpenAI está configurada corretamente."

    else:
        # Unknown file type
        transcript = f"[TIPO DE ARQUIVO NÃO SUPORTADO]\n\nTipo de arquivo: {file_ext}\n\nFormatos suportados: .txt, .md, .mp3, .wav, .mp4, .avi, .mov, .m4a"
        logger.warning(f"Tipo de arquivo não suportado: {file_ext}")

    # Generate markdown summary using AI
    update_progress(session_id, 60, "Gerando resumo com IA...")
    summary = generate_meeting_summary(transcript, participants, meeting_date, meeting_title, session_id)

    return summary


def _is_error_transcript(transcript: str) -> bool:
    """Detecta se a transcrição representa uma mensagem de erro."""
    if not transcript:
        return True

    stripped = transcript.lstrip()
    known_error_prefixes = (
        "[ERRO",
        "[TIPO",
        "[MODO",
        "[DEMONSTRACAO",
        "[MODO DE DEMONSTRAÇÃO",
    )
    return any(stripped.startswith(prefix) for prefix in known_error_prefixes)


def generate_meeting_summary(transcript: str, participants: str, meeting_date: str, meeting_title: str, session_id: str) -> str:
    """
    Generate a structured meeting summary in markdown format using OpenAI GPT.
    """
    formatted_date = meeting_date if meeting_date else "Data não informada"
    formatted_participants = participants if participants else "Participantes não informados"

    # Use OpenAI GPT for intelligent summarization if available
    client = get_openai_client()
    if client and transcript and not _is_error_transcript(transcript):
        try:
            logger.info("Gerando resumo com OpenAI GPT...")

            # Load prompt from file
            prompt_file = APP_ROOT / "prompts" / "prompt_resumo.md"
            if not prompt_file.exists():
                logger.warning(f"Prompt file não encontrado: {prompt_file}, usando fallback template")
                raise FileNotFoundError(f"Prompt file não encontrado: {prompt_file}")
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()

            prompt = prompt_template.replace('<<DATA>>', formatted_date)
            prompt = prompt.replace('<<NOMES>>', formatted_participants)
            prompt = prompt.replace('<<PARTICIPANTES_INTERNOS>>', formatted_participants)
            prompt = prompt.replace('<<TRANSCRIÇÂO>>', transcript[:4000])
            prompt = prompt.replace(' <<TRANSCRIÇÂO >>', transcript[:4000])

            models_to_try = get_model_candidates()

            for model_name in models_to_try:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "Você é um especialista em resumir reuniões de negócios de forma clara e profissional."},
                            {"role": "user", "content": prompt}
                        ],
                        max_completion_tokens=4000
                    )

                    ai_summary = response.choices[0].message.content
                    logger.info(f"Resumo gerado com sucesso pelo OpenAI GPT (modelo {model_name})")
                    update_progress(session_id, 75, "Resumo gerado com sucesso")

                    # Retornar apenas o resumo da IA (sem header duplicado - já está na capa)
                    return ai_summary

                except Exception as api_error:
                    logger.error(f"Erro ao gerar resumo com OpenAI (modelo {model_name}): {api_error}")
                    continue

        except Exception as e:
            logger.error(f"Erro inesperado ao preparar o prompt para OpenAI: {e}")
            # Fall back to template-based summary

    # Fallback template-based summary
    logger.info("Usando template padrão para resumo")

    summary_md = f"""# {meeting_title}

**Data:** {formatted_date}
**Participantes:** {formatted_participants}

## Resumo Executivo

{'Este resumo foi gerado automaticamente a partir da transcrição da reunião.' if not transcript.startswith('[') else 'Modo de demonstração - integração completa com IA disponível com chave OpenAI.'}

## Pontos Principais Discutidos

### Tópicos Abordados
- Principais assuntos tratados na reunião
- Discussões relevantes para os objetivos

### Participação
- Contribuições dos participantes
- Pontos de vista apresentados

## Ações e Responsáveis

| Ação | Responsável | Prazo |
|------|-------------|--------|
| A definir com base na discussão | Participantes | A combinar |

## Próximos Passos

**Próxima Reunião:** A definir
**Acompanhamento:** Verificar progresso das ações definidas

---

*Resumo gerado automaticamente em {formatted_date}*
"""

    return summary_md
