"""
Rotas para processamento de reuniões e geração de resumos em PDF.

O fluxo tenta usar Whisper para transcrição e OpenAI para síntese. Se uma dessas
integrações não estiver disponível, o endpoint ainda gera um resumo padrão.
"""

from flask import Blueprint, request, send_file, abort, jsonify, current_app
from pathlib import Path
import tempfile
import traceback
import logging
import uuid
import whisper
from openai import OpenAI
import os

from app.utils.md_to_pdf import md_to_pdf
from app.routes.progress import update_progress

meeting_bp = Blueprint('meeting', __name__)
logger = logging.getLogger(__name__)

# Diretório raiz do projeto para prompt, logo e imagem de capa.
APP_ROOT = Path(__file__).resolve().parent.parent.parent

# Cliente OpenAI opcional: a rota funciona sem ele, mas perde o resumo com IA.
openai_api_key = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
if openai_api_key:
    openai_client = OpenAI(api_key=openai_api_key)
    logger.info(f"OpenAI API configurada. Modelo: {OPENAI_MODEL}")
else:
    openai_client = None
    logger.warning("OPENAI_API_KEY não encontrada - usando modo de demonstração")

# O modelo Whisper é carregado no import para evitar re-load a cada request.
try:
    whisper_model_name = os.getenv('WHISPER_MODEL', 'base')
    whisper_model = whisper.load_model(whisper_model_name)
    logger.info(f"Modelo Whisper '{whisper_model_name}' carregado com sucesso")
except Exception as e:
    whisper_model = None
    logger.error(f"Erro ao carregar modelo Whisper: {e}")


@meeting_bp.route("/process-meeting", methods=["POST"])
def process_meeting():
    """Processa texto/áudio/vídeo de reunião e retorna um PDF com o resumo."""
    session_id = request.form.get('session_id', str(uuid.uuid4()))
    try:
        logger.info("=== INICIO DO PROCESSAMENTO DE REUNIÃO ===")
        update_progress(session_id, 5, "Iniciando processamento...")

        meeting_file = request.files.get("meeting_file")
        if not meeting_file:
            logger.error("Nenhum arquivo de reunião enviado")
            abort(400, "Nenhum arquivo de reunião enviado")

        filename = Path(meeting_file.filename or "meeting").name
        logger.info(f"Arquivo de reunião recebido: {filename}")
        logger.info(f"Tipo de conteúdo: {meeting_file.content_type}")

        # Metadados usados tanto no resumo quanto na capa do PDF.
        participants = request.form.get('meeting_participants', '')
        meeting_date = request.form.get('meeting_date', '')
        meeting_title = request.form.get('meeting_title', '') or 'Resumo de Reunião'

        logger.info(f"Participantes: {participants}")
        logger.info(f"Data: {meeting_date}")
        logger.info(f"Título: {meeting_title}")

        # No fluxo de reunião, subtítulo e descrição da capa são derivados da reunião.
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

            # Gera um Markdown intermediário antes de reaproveitar o mesmo gerador de PDF.
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
                download_name=f"{meeting_title.replace(' ', '_')}.pdf",
            )

    except Exception as e:
        logger.error(f"ERRO DURANTE PROCESSAMENTO DE REUNIÃO: {str(e)}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


def process_meeting_file(file_path: Path, participants: str, meeting_date: str, meeting_title: str, session_id: str) -> str:
    """
    Processa um arquivo de reunião e devolve o resumo final em Markdown.

    Tipos aceitos atualmente:
    - texto: `.txt`, `.md`
    - mídia: `.mp3`, `.wav`, `.mp4`, `.avi`, `.mov`, `.m4a`
    """
    logger.info(f"Processando arquivo de reunião: {file_path}")

    # Determina se o fluxo lê texto diretamente ou dispara transcrição.
    file_ext = file_path.suffix.lower()

    transcript = ""

    if file_ext in ['.txt', '.md']:
        # Texto pronto: sem Whisper.
        update_progress(session_id, 25, "Lendo arquivo de texto...")
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        logger.info("Arquivo de texto lido diretamente")

    elif file_ext in ['.mp3', '.wav', '.mp4', '.avi', '.mov', '.m4a']:
        # Áudio/vídeo: depende do modelo Whisper carregado no boot.
        if whisper_model:
            try:
                update_progress(session_id, 25, "Transcrevendo áudio...")
                logger.info("Iniciando transcrição com Whisper...")
                result = whisper_model.transcribe(str(file_path), language="pt")
                transcript = result["text"]
                logger.info(f"Transcrição concluída. Tamanho: {len(transcript)} caracteres")
                update_progress(session_id, 50, "Transcrição concluída")
            except Exception as e:
                logger.error(f"Erro na transcrição Whisper: {e}")
                transcript = f"[ERRO NA TRANSCRIÇÃO]\n\nArquivo: {file_path.name}\nErro: {str(e)}\n\nPor favor, tente novamente ou use um arquivo de texto."
        else:
            transcript = f"[WHISPER NÃO DISPONÍVEL]\n\nArquivo de áudio/vídeo detectado: {file_path.name}\n\nO modelo Whisper não foi carregado corretamente. Verifique as dependências."
            logger.warning("Whisper não disponível para transcrição")

    else:
        # Mantém o retorno em Markdown mesmo em caso de formato não suportado.
        transcript = f"[TIPO DE ARQUIVO NÃO SUPORTADO]\n\nTipo de arquivo: {file_ext}\n\nFormatos suportados: .txt, .md, .mp3, .wav, .mp4, .avi, .mov, .m4a"
        logger.warning(f"Tipo de arquivo não suportado: {file_ext}")

    # A etapa final sempre produz Markdown, com IA ou com template fallback.
    update_progress(session_id, 60, "Gerando resumo com IA...")
    summary = generate_meeting_summary(transcript, participants, meeting_date, meeting_title, session_id)

    return summary


def generate_meeting_summary(transcript: str, participants: str, meeting_date: str, meeting_title: str, session_id: str) -> str:
    """
    Gera um resumo estruturado em Markdown.

    Quando a OpenAI está configurada, usa `prompts/prompt_resumo.md` e envia
    até os primeiros 4000 caracteres da transcrição. Em caso de falha, volta
    para um template estático que preserva o restante do fluxo.
    """
    formatted_date = meeting_date if meeting_date else "Data não informada"
    formatted_participants = participants if participants else "Participantes não informados"

    # Só chama a OpenAI quando há cliente configurado e a transcrição é utilizável.
    if openai_client and transcript and not transcript.startswith('['):
        try:
            logger.info("Gerando resumo com OpenAI GPT...")

            # O prompt fica versionado no repositório para facilitar ajustes editoriais.
            prompt_file = APP_ROOT / "prompts" / "prompt_resumo.md"
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()

            prompt = prompt_template.replace('<<DATA>>', formatted_date)
            prompt = prompt.replace('<<NOMES>>', formatted_participants)
            prompt = prompt.replace('<<PARTICIPANTES_INTERNOS>>', formatted_participants)
            prompt = prompt.replace('<<TRANSCRIÇÂO>>', transcript[:4000])
            prompt = prompt.replace(' <<TRANSCRIÇÂO >>', transcript[:4000])

            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um especialista em resumir reuniões de negócios de forma clara e profissional."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=4000
            )

            ai_summary = response.choices[0].message.content
            logger.info("Resumo gerado com sucesso pelo OpenAI GPT")
            update_progress(session_id, 75, "Resumo gerado com sucesso")

            # O PDF final parte deste Markdown intermediário.
            summary_md = f"""# {meeting_title}

**Data:** {formatted_date}
**Participantes:** {formatted_participants}

{ai_summary}

---

*Resumo gerado automaticamente com IA em {formatted_date}*
"""

            return summary_md

        except Exception as e:
            logger.error(f"Erro ao gerar resumo com OpenAI: {e}")
            # Qualquer falha na OpenAI cai para o template padrão abaixo.

    # Template padrão para quando IA ou transcrição não estão disponíveis.
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
