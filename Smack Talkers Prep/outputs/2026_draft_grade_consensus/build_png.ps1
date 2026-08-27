Add-Type -AssemblyName System.Drawing

$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$paths = @(
    (Join-Path $base 'overall_summary.png'),
    (Join-Path $base 'snake_consensus.png'),
    (Join-Path $base 'auction_consensus.png')
)
$images = @($paths | ForEach-Object { [System.Drawing.Image]::FromFile($_) })
$gutter = 28
$canvasWidth = [int](($images | ForEach-Object { $_.Width } | Measure-Object -Maximum).Maximum)
$imageHeight = [int](($images | ForEach-Object { $_.Height } | Measure-Object -Sum).Sum)
$canvasHeight = [int]($imageHeight + ($gutter * ($images.Count - 1)))
$bitmap = [System.Drawing.Bitmap]::new($canvasWidth, $canvasHeight)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.Clear([System.Drawing.Color]::White)
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

$y = 0
for ($index = 0; $index -lt $images.Count; $index++) {
    $image = $images[$index]
    $x = [int](($canvasWidth - $image.Width) / 2)
    $graphics.DrawImage($image, $x, $y, $image.Width, $image.Height)
    $y += $image.Height
    if ($index -lt $images.Count - 1) {
        $separatorY = $y + [int]($gutter / 2)
        $pen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(210, 219, 228), 2)
        $graphics.DrawLine($pen, 56, $separatorY, $canvasWidth - 56, $separatorY)
        $pen.Dispose()
        $y += $gutter
    }
}

$output = Join-Path $base 'Smack_Talkers_2026_Consensus_Draft_Grades.png'
$bitmap.Save($output, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
$images | ForEach-Object { $_.Dispose() }
Write-Output $output
