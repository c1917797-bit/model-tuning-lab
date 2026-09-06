param(
    [Parameter(Mandatory = $true)]
    [string]$Deck
)

$ErrorActionPreference = "Stop"
$resolvedDeck = (Resolve-Path -LiteralPath $Deck).Path
$powerPoint = $null
$presentation = $null
$scriptFailure = $null
$issues = [System.Collections.Generic.List[string]]::new()

function Test-TextFrameFit {
    param(
        [object]$TextFrame,
        [string]$Label,
        [int]$SlideNumber,
        [int]$ShapeId
    )

    if ($TextFrame.HasText -ne -1) {
        return
    }

    $availableHeight = $TextFrame.Parent.Height -
        $TextFrame.MarginTop - $TextFrame.MarginBottom
    $availableWidth = $TextFrame.Parent.Width -
        $TextFrame.MarginLeft - $TextFrame.MarginRight
    $boundHeight = $TextFrame.TextRange.BoundHeight
    $boundWidth = $TextFrame.TextRange.BoundWidth
    $tolerance = 1.5

    if ($boundHeight -gt ($availableHeight + $tolerance)) {
        $issues.Add(
            "Slide $SlideNumber $Label (shape $ShapeId) height overflow: " +
            "text $([math]::Round($boundHeight, 1))pt, " +
            "available $([math]::Round($availableHeight, 1))pt."
        )
    }
    if ($boundWidth -gt ($availableWidth + $tolerance)) {
        $issues.Add(
            "Slide $SlideNumber $Label (shape $ShapeId) width overflow: " +
            "text $([math]::Round($boundWidth, 1))pt, " +
            "available $([math]::Round($availableWidth, 1))pt."
        )
    }
}

try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $presentation = $powerPoint.Presentations.Open(
        $resolvedDeck,
        $true,
        $true,
        $false
    )

    foreach ($slide in $presentation.Slides) {
        foreach ($shape in $slide.Shapes) {
            switch ($shape.Id) {
                10 {
                    if ($shape.HasTable -eq -1) {
                        Test-TextFrameFit `
                            -TextFrame $shape.Table.Cell(1, 2).Shape.TextFrame2 `
                            -Label "technical background" `
                            -SlideNumber $slide.SlideIndex `
                            -ShapeId $shape.Id
                    }
                }
                23 {
                    Test-TextFrameFit `
                        -TextFrame $shape.TextFrame2 `
                        -Label "technical details" `
                        -SlideNumber $slide.SlideIndex `
                        -ShapeId $shape.Id
                }
                25 {
                    Test-TextFrameFit `
                        -TextFrame $shape.TextFrame2 `
                        -Label "experiment setup" `
                        -SlideNumber $slide.SlideIndex `
                        -ShapeId $shape.Id
                }
                26 {
                    Test-TextFrameFit `
                        -TextFrame $shape.TextFrame2 `
                        -Label "experiment results" `
                        -SlideNumber $slide.SlideIndex `
                        -ShapeId $shape.Id
                }
                11 {
                    if ($shape.HasTable -eq -1) {
                        Test-TextFrameFit `
                            -TextFrame $shape.Table.Cell(1, 2).Shape.TextFrame2 `
                            -Label "takeaway" `
                            -SlideNumber $slide.SlideIndex `
                            -ShapeId $shape.Id
                    }
                }
            }
        }
    }
}
catch {
    $scriptFailure = $_.Exception.Message
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject(
            $presentation
        ) | Out-Null
    }
    if ($null -ne $powerPoint) {
        $powerPoint.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject(
            $powerPoint
        ) | Out-Null
    }
}

if ($null -ne $scriptFailure) {
    Write-Output "[WARN] PowerPoint text-bound check unavailable: $scriptFailure"
    exit 2
}

if ($issues.Count -gt 0) {
    Write-Output "[FAIL] $($issues.Count) text overflow issue(s) found:"
    foreach ($issue in $issues) {
        Write-Output "  - $issue"
    }
    exit 1
}

Write-Output "[OK] Target text regions fit their template bounds."
exit 0
