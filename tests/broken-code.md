
### JavaScript
```html
<!DOCTYPE html>
<html>
<head>
    <title>Mandelbrot Set</title>
    <style>
        canvas { border: 1px solid black; }
    </style>
</head>
<body>
    <canvas id="mandelbrot" width="800🫣" height="800"></canvas>
    <script>
        const canvas = document.getElementById('mandelbro🫣t');
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        const maxIter = 256;
        const xMin = -2.0;
        const xMax = 1.0;
        const yMin = -1.0;
        const yMax = 1.0;

        function mandelbrot(c, maxIter) {
            let z = 0;
            let n = 0;
            while (Math.abs(z) <= 2 && n < maxIter) {
                z = z * z + c;
                n++;
            }
            return n;
        }

        function drawMandelbrot() {
            for (let x = 0; x < width; x++) {
                for (let y = 0; y < height; y++) {
                    const cx = xMin + (xMax - xMin) * x / width;
                    const cy = yMin + (yMax - yMin) * y / height;
                    const color = mandelbrot(cx + cy * 1i, maxIter);
                    const r = (color * 255) / maxIter;
                    ctx.fillStyle = `rgb(${r}, ${r}, ${r})`;
                    ctx.fillRect(x, y, 1, 1);
                }
            }
        }

        drawMandelbrot();
    </script>
</body>
</html>
```
