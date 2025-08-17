# scripts\show_tree.ps1
<#
.SYNOPSIS
    show-tree.ps1

.DESCRIPTION
    Viser en trevisning av mapper og filer med størrelser i MB, med Unicode box drawing.
    Ignorerer 'node_modules' og '.git' som standard.

.PARAMETER Path
    Startsti for trevisningen. Default er nåværende mappe ('.').

.PARAMETER IgnoreDirs
    Liste over foldere du vil ignorere i tillegg til standard (node_modules, .git).

.EXAMPLE
    Standard:
        .\show_tree.ps1

    Med flere ignorerte foldere:
        .\show_tree.ps1 -IgnoreDirs @("dist", ".vscode")

.NOTES
    For pen prosjekt-trevisning med størrelser.
#>

param (
    [string]$Path = ".",
    [string[]]$IgnoreDirs = @()
)

# Standard ignorerte foldere
$defaultIgnores = @("node_modules", ".git")
$IgnoreDirs = $IgnoreDirs + $defaultIgnores | Select-Object -Unique

# Unicode box drawing characters
$TreeLast = "$([char]0x2514)$([char]0x2500)$([char]0x2500) "     # └── 
$TreeItem = "$([char]0x251C)$([char]0x2500)$([char]0x2500) "     # ├── 
$TreeLine = "$([char]0x2502)   "                                 # │   
$TreeSpace = "    "                                              #     

function Get-DirectoryTree {
    param (
        [string]$Folder,
        [string]$Prefix = "",
        [string[]]$IgnoreDirs
    )

    # Hent filer og foldere i denne mappen
    $items = Get-ChildItem -Path $Folder -Force -ErrorAction SilentlyContinue | Where-Object {
        -not ($IgnoreDirs -contains $_.Name)
    }

    # Sorter: foldere først, så filer
    $items = $items | Sort-Object { if ($_.PSIsContainer) {0} else {1} }, Name

    for ($i = 0; $i -lt $items.Count; $i++) {
        $item = $items[$i]
        $isLast = ($i -eq $items.Count - 1)

        # Velg riktig tree character
        $treeChar = if ($isLast) { $TreeLast } else { $TreeItem }
        $newPrefix = if ($isLast) { $Prefix + $TreeSpace } else { $Prefix + $TreeLine }

        if ($item.PSIsContainer) {
            # Beregn mappe-størrelse
            try {
                $size = (Get-ChildItem -Path $item.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            } catch {
                $size = 0
            }
            $sizeMB = [Math]::Round($size / 1MB, 2)
            Write-Output ($Prefix + $treeChar + $item.Name + "/ (" + $sizeMB + " MB)")

            # Rekursivt kall
            Get-DirectoryTree -Folder $item.FullName -Prefix $newPrefix -IgnoreDirs $IgnoreDirs
        }
        else {
            # Filstørrelse
            $sizeMB = [Math]::Round($item.Length / 1MB, 2)
            Write-Output ($Prefix + $treeChar + $item.Name + " (" + $sizeMB + " MB)")
        }
    }
}

# Startpunkt
Write-Output ("Directory tree for: " + (Resolve-Path $Path))
Get-DirectoryTree -Folder (Resolve-Path $Path) -Prefix "" -IgnoreDirs $IgnoreDirs