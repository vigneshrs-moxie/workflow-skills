# The Windows twin of install.sh. Links this repo's skills and agents into %USERPROFILE%\.claude so
# Claude Code picks them up, and clones (or updates) the git workflow docs the Foreman follows.
# Run it from PowerShell:   powershell -ExecutionPolicy Bypass -File install.ps1
# Re-run any time. Folders get a junction (no admin rights needed), so `git pull` here updates them
# at once. Files get a symbolic link when Windows allows one (Developer Mode or an admin window),
# else a copy; copies don't follow `git pull`, so run this again after one.
# The list of links is read from install.sh (its "# link:" lines), so the two scripts make the same links.
# Anything already at a target that isn't this repo's link (or an up-to-date copy) is moved to
# %USERPROFILE%\.claude\backups\claude-feature-workflow\ (outside skills\, so Claude Code won't load it twice).
$ErrorActionPreference = 'Stop'
$Here = $PSScriptRoot
$ClaudeDir = if ($env:CLAUDE_DIR) { $env:CLAUDE_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$GitDocsDir = if ($env:GIT_DOCS_DIR) { $env:GIT_DOCS_DIR } else { Join-Path $env:USERPROFILE 'Projects\moxie-portal-git-workflow' }
$GitDocsRepo = 'https://github.com/vigneshrs-moxie/moxie-portal-git-workflow.git'
$BackupDir = Join-Path $ClaudeDir ('backups\claude-feature-workflow\' + (Get-Date -Format 'yyyy-MM-dd-HHmmss'))

function Same-Path($a, $b) {
  if (-not $a -or -not $b) { return $false }
  return ([IO.Path]::GetFullPath($a).TrimEnd('\') -ieq [IO.Path]::GetFullPath($b).TrimEnd('\'))
}

function Link-Item($Src, $Dst, [bool]$IsFolder) {
  $item = Get-Item -LiteralPath $Dst -Force -ErrorAction SilentlyContinue
  if ($item) {
    if ($item.LinkType -and (Same-Path (@($item.Target)[0]) $Src)) { Write-Output "ok       $Dst"; return }
    if (-not $IsFolder -and -not $item.LinkType -and -not $item.PSIsContainer -and
        (Get-FileHash -LiteralPath $Dst).Hash -eq (Get-FileHash -LiteralPath $Src).Hash) { Write-Output "ok       $Dst (a copy)"; return }
    $to = Join-Path $BackupDir (Split-Path -Leaf (Split-Path -Parent $Dst))
    New-Item -ItemType Directory -Force -Path $to | Out-Null
    Move-Item -LiteralPath $Dst -Destination $to
    Write-Output "backed up $Dst -> $BackupDir\"
  }
  if ($IsFolder) {
    New-Item -ItemType Junction -Path $Dst -Target $Src | Out-Null
    Write-Output "linked   $Dst"
    return
  }
  try {
    New-Item -ItemType SymbolicLink -Path $Dst -Target $Src -ErrorAction Stop | Out-Null
    Write-Output "linked   $Dst"
  } catch {
    Copy-Item -LiteralPath $Src -Destination $Dst
    Write-Output "copied   $Dst (Windows didn't allow a link here; run this again after a git pull)"
  }
}

# "# link: skills/*/ -> skills": a pattern in this repo -> a folder under .claude. A trailing / means folders.
$links = Get-Content -LiteralPath (Join-Path $Here 'install.sh') | Where-Object { $_ -match '^# link: (\S+) -> (\S+)\s*$' } | ForEach-Object {
  if ($_ -match '^# link: (\S+) -> (\S+)\s*$') { [pscustomobject]@{ Pattern = $Matches[1]; Folder = $Matches[2] } }
}
if (-not $links) { throw "No '# link:' lines found in install.sh." }

foreach ($l in $links) {
  $isFolder = $l.Pattern.EndsWith('/')
  $pattern = Join-Path $Here ($l.Pattern.TrimEnd('/') -replace '/', '\')
  $target = Join-Path $ClaudeDir ($l.Folder -replace '/', '\')
  New-Item -ItemType Directory -Force -Path $target | Out-Null
  $found = if ($isFolder) { Get-ChildItem -Path $pattern -Directory } else { Get-ChildItem -Path $pattern -File }
  foreach ($src in ($found | Sort-Object Name)) { Link-Item $src.FullName (Join-Path $target $src.Name) $isFolder }
}

# The git workflow docs (branches, PR stages, releases) the Foreman reads first.
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Output "skipped  $GitDocsDir : git isn't installed. Install Git for Windows, then run this again."
} elseif (Test-Path -LiteralPath (Join-Path $GitDocsDir '.git')) {
  git -C $GitDocsDir pull --ff-only -q
  if ($LASTEXITCODE -eq 0) { Write-Output "updated  $GitDocsDir" } else { Write-Output "couldn't update $GitDocsDir (git pull failed; see above)" }
} elseif (Test-Path -LiteralPath $GitDocsDir) {
  Write-Output "skipped  $GitDocsDir exists but isn't a git clone. Rename it, then run this again."
} else {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $GitDocsDir) | Out-Null
  git clone -q $GitDocsRepo $GitDocsDir
  if ($LASTEXITCODE -eq 0) { Write-Output "cloned   $GitDocsDir" } else { Write-Output "couldn't clone $GitDocsRepo (see above)" }
}

Write-Output 'Done. Open Claude Code in your project and type /feature to start.'
