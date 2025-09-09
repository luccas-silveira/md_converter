#!/usr/bin/env python3
"""
Script para testar e diagnosticar problemas do WeasyPrint
"""

import sys
import os

def test_imports():
    """Testa se todas as dependências estão funcionando"""
    print("=== Testando imports ===")
    
    try:
        import weasyprint
        print(f"✓ WeasyPrint {weasyprint.__version__}")
    except ImportError as e:
        print(f"✗ WeasyPrint: {e}")
        return False
    
    try:
        import pydyf
        print(f"✓ pydyf {pydyf.__version__}")
    except ImportError as e:
        print(f"✗ pydyf: {e}")
        return False
    
    try:
        import cssselect2
        print(f"✓ cssselect2 {cssselect2.__version__}")
    except ImportError as e:
        print(f"✗ cssselect2: {e}")
        return False
    
    try:
        import tinycss2
        print(f"✓ tinycss2 {tinycss2.__version__}")
    except ImportError as e:
        print(f"✗ tinycss2: {e}")
        return False
    
    return True

def test_simple_pdf():
    """Testa criação de PDF simples"""
    print("\n=== Testando criação de PDF ===")
    
    try:
        from weasyprint import HTML, CSS
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>Teste WeasyPrint</h1>
            <p>Se você está vendo este PDF, o WeasyPrint está funcionando!</p>
        </body>
        </html>
        """
        
        html = HTML(string=html_content)
        pdf_bytes = html.write_pdf()
        
        print(f"✓ PDF criado com sucesso ({len(pdf_bytes)} bytes)")
        
        # Salvar arquivo de teste
        with open('teste_weasyprint.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print("✓ Arquivo teste_weasyprint.pdf salvo")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao criar PDF: {e}")
        import traceback
        print("Traceback completo:")
        print(traceback.format_exc())
        return False

def test_markdown_conversion():
    """Testa conversão completa de Markdown"""
    print("\n=== Testando conversão Markdown ===")
    
    try:
        import markdown2
        from weasyprint import HTML
        
        md_content = """
# Teste de Markdown

Este é um **teste** de conversão de Markdown para PDF.

## Lista de itens:

- Item 1
- Item 2  
- Item 3

Código inline: `print("Hello World")`

```python
def hello():
    print("Hello from code block!")
```
        """
        
        html_content = markdown2.markdown(md_content, extras=['fenced-code-blocks'])
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                code {{ background: #f4f4f4; padding: 2px 4px; }}
                pre {{ background: #f4f4f4; padding: 10px; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        html = HTML(string=full_html)
        pdf_bytes = html.write_pdf()
        
        print(f"✓ Conversão Markdown->PDF ok ({len(pdf_bytes)} bytes)")
        
        with open('teste_markdown.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print("✓ Arquivo teste_markdown.pdf salvo")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro na conversão Markdown: {e}")
        import traceback
        print("Traceback completo:")
        print(traceback.format_exc())
        return False

def check_system_dependencies():
    """Verifica dependências do sistema"""
    print("\n=== Verificando dependências do sistema ===")
    
    try:
        import ctypes.util
        
        libs_to_check = [
            'cairo',
            'pango-1.0', 
            'pangocairo-1.0',
            'gdk_pixbuf-2.0'
        ]
        
        for lib in libs_to_check:
            lib_path = ctypes.util.find_library(lib)
            if lib_path:
                print(f"✓ {lib}: {lib_path}")
            else:
                print(f"✗ {lib}: não encontrada")
                
    except Exception as e:
        print(f"Erro ao verificar bibliotecas: {e}")

def main():
    print("🔍 Diagnóstico WeasyPrint")
    print("=" * 50)
    
    # Informações do sistema
    print(f"Python: {sys.version}")
    print(f"Plataforma: {sys.platform}")
    print(f"Diretório atual: {os.getcwd()}")
    
    # Testes
    success = True
    success &= test_imports()
    
    if success:
        check_system_dependencies()
        success &= test_simple_pdf()
        success &= test_markdown_conversion()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Todos os testes passaram! WeasyPrint está funcionando.")
    else:
        print("❌ Há problemas com o WeasyPrint. Verifique os erros acima.")
        
        print("\n🔧 Possíveis soluções:")
        print("1. Reinstalar com versões específicas:")
        print("   pip uninstall weasyprint pydyf -y")
        print("   pip install weasyprint==60.2 pydyf==0.10.0")
        print("\n2. No Ubuntu/Debian:")
        print("   sudo apt-get update")
        print("   sudo apt-get install libcairo2-dev libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0")
        print("\n3. Limpar cache do pip:")
        print("   pip cache purge")

if __name__ == "__main__":
    main()