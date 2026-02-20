# Busca y muestra archivos con 'import fitz', propone reemplazo seguro.
Get-ChildItem -Path .. -Recurse -Include *.py | ForEach-Object {
    $file = $_.FullName
    $content = Get-Content $file
    if ($content -match 'import fitz') {
        Write-Host "Archivo: $file"
        Write-Host "Cambio propuesto: 'import fitz' → 'import pymupdf as fitz'"
    }
}
Write-Host "Modo seguro: Solo muestra cambios, no modifica archivos."
