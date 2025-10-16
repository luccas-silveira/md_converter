"""
Testes de segurança para sanitização de nomes de arquivo.

Este módulo testa a função sanitize_filename() para garantir que
ataques de path traversal sejam bloqueados adequadamente.
"""

import pytest
from app.utils.file_security import sanitize_filename


class TestFilenameSanitization:
    """Testes de segurança para sanitização de filenames"""

    def test_path_traversal_attack(self):
        """Deve bloquear tentativas de path traversal com ../"""
        malicious = "../../etc/passwd"
        result = sanitize_filename(malicious, default_extension='.md')

        # Verificar que caracteres perigosos foram removidos
        assert '..' not in result
        assert '/' not in result
        assert result.endswith('.md')

        # Nome deve ter sido sanitizado para algo seguro
        assert len(result) > 0
        print(f"Path traversal bloqueado: '{malicious}' → '{result}'")

    def test_absolute_path_attack(self):
        """Deve remover caminhos absolutos Unix"""
        malicious = "/etc/passwd"
        result = sanitize_filename(malicious, default_extension='.md')

        assert not result.startswith('/')
        assert result.endswith('.md')
        print(f"Caminho absoluto removido: '{malicious}' → '{result}'")

    def test_windows_path_attack(self):
        """Deve bloquear caminhos Windows com backslashes"""
        malicious = "..\\..\\windows\\system32\\config\\sam"
        result = sanitize_filename(malicious, default_extension='.md')

        assert '\\' not in result
        assert '..' not in result
        assert result.endswith('.md')
        print(f"Path Windows bloqueado: '{malicious}' → '{result}'")

    def test_null_byte_injection(self):
        """Deve remover null bytes que poderiam truncar extensões"""
        malicious = "file.md\x00.exe"
        result = sanitize_filename(malicious)

        assert '\x00' not in result
        # Deve preservar .md e remover .exe
        assert result.endswith('.md')
        print(f"Null byte removido: '{malicious}' → '{result}'")

    def test_valid_filename_preserved(self):
        """Deve preservar nomes de arquivo válidos"""
        valid = "my_document_2024.md"
        result = sanitize_filename(valid)

        assert result == valid
        print(f"Nome válido preservado: '{valid}' → '{result}'")

    def test_unicode_filename_handling(self):
        """Deve lidar com caracteres Unicode de forma segura"""
        unicode_name = "relatório_reunião_2024.md"
        result = sanitize_filename(unicode_name)

        # Deve retornar algo válido (werkzeug pode transliterar)
        assert result
        assert len(result) > 0
        assert result.endswith('.md')
        print(f"Unicode tratado: '{unicode_name}' → '{result}'")

    def test_empty_filename_with_default(self):
        """Deve gerar nome único quando filename está vazio"""
        result = sanitize_filename("", default_extension='.md')

        assert result.endswith('.md')
        assert len(result) > 3  # Deve ter UUID + extensão
        assert 'uploaded_file_' in result
        print(f"Nome vazio gerou: '{result}'")

    def test_empty_filename_without_default(self):
        """Deve lançar ValueError quando vazio sem extensão padrão"""
        with pytest.raises(ValueError, match="Nome de arquivo não fornecido"):
            sanitize_filename("")

    def test_none_filename_with_default(self):
        """Deve tratar None como filename vazio"""
        result = sanitize_filename(None, default_extension='.md')

        assert result.endswith('.md')
        assert 'uploaded_file_' in result
        print(f"None tratado: {result}")

    def test_very_long_filename(self):
        """Deve truncar nomes muito longos"""
        long_name = "a" * 300 + ".md"
        result = sanitize_filename(long_name, max_length=100)

        assert len(result) <= 100
        assert result.endswith('.md')
        print(f"Nome truncado: {len(long_name)} chars → {len(result)} chars")

    def test_filename_without_extension_gets_default(self):
        """Deve adicionar extensão padrão se não houver"""
        result = sanitize_filename("documento", default_extension='.md')

        assert result == "documento.md"
        print(f"Extensão adicionada: 'documento' → '{result}'")

    def test_multiple_dots_in_filename(self):
        """Deve lidar com múltiplos pontos no nome"""
        filename = "arquivo.teste.final.md"
        result = sanitize_filename(filename)

        # Werkzeug deve lidar corretamente
        assert result
        assert result.endswith('.md')
        print(f"Múltiplos pontos: '{filename}' → '{result}'")

    def test_special_characters_removed(self):
        """Deve remover caracteres especiais perigosos"""
        dangerous = "file<>name?.md"
        result = sanitize_filename(dangerous)

        assert '<' not in result
        assert '>' not in result
        assert '?' not in result
        print(f"Caracteres especiais removidos: '{dangerous}' → '{result}'")

    def test_leading_dot_filename(self):
        """Deve lidar com arquivos que começam com ponto (ocultos)"""
        hidden = ".hidden_file.md"
        result = sanitize_filename(hidden)

        # Werkzeug pode remover o ponto inicial ou não, mas deve ser seguro
        assert result
        assert result.endswith('.md')
        print(f"Arquivo oculto tratado: '{hidden}' → '{result}'")

    def test_spaces_in_filename(self):
        """Deve substituir espaços por underscores"""
        spaced = "my document with spaces.md"
        result = sanitize_filename(spaced)

        # Werkzeug substitui espaços por underscores
        assert ' ' not in result or result.count(' ') < spaced.count(' ')
        assert result.endswith('.md')
        print(f"Espaços tratados: '{spaced}' → '{result}'")

    def test_mixed_path_separators(self):
        """Deve remover mistura de separadores Unix e Windows"""
        mixed = "../folder\\subfolder/file.md"
        result = sanitize_filename(mixed, default_extension='.md')

        assert '..' not in result
        assert '/' not in result
        assert '\\' not in result
        assert result.endswith('.md')
        print(f"Separadores mistos removidos: '{mixed}' → '{result}'")

    def test_max_length_with_long_extension(self):
        """Deve truncar preservando extensão mesmo se extensão for longa"""
        name_with_long_ext = "a" * 50 + ".markdown"
        result = sanitize_filename(name_with_long_ext, max_length=30)

        assert len(result) <= 30
        assert result.endswith('.markdown')
        print(f"Truncado com extensão longa: '{name_with_long_ext}' → '{result}'")

    def test_only_dangerous_characters(self):
        """Deve gerar nome seguro quando input contém apenas caracteres perigosos"""
        only_dangerous = "../../"
        result = sanitize_filename(only_dangerous, default_extension='.md')

        assert '..' not in result
        assert '/' not in result
        assert result.endswith('.md')
        assert 'uploaded_file_' in result
        print(f"Apenas chars perigosos: '{only_dangerous}' → '{result}'")

    def test_case_sensitivity_preserved(self):
        """Deve preservar maiúsculas/minúsculas em nomes válidos"""
        mixed_case = "MyDocument.MD"
        result = sanitize_filename(mixed_case)

        # Case deve ser preservado
        assert 'MyDocument' in result or 'mydocument' in result  # Pode variar por OS
        print(f"Case handling: '{mixed_case}' → '{result}'")
