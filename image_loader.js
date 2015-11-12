window.canvas = document.getElementById('canvas');
window.ctx = canvas.getContext('2d');

// function requires an element: <input type="file" id="imgLoader">
// loads image into window.orig_im, then draws image on variable
// window.canvas. Then captures imgdata as window.im (pure uint8 data)
document.getElementById('imgLoader').onchange = function handleImage(e) {
    var reader = new FileReader();
    reader.onload = function (event) { console.log('fdsf');
        window.orig_im = new Image();
        orig_im.src = event.target.result;
        orig_im.onload = function () {
            resizeCanvasToImage(canvas, orig_im); 
            ctx.drawImage(orig_im, 0, 0);
            save_canvas_imgdata(canvas);
        }
    }
    reader.readAsDataURL(e.target.files[0]);
}

function resizeCanvasToImage(canvas, image) {
    //resizes canvas internally so that full image is displayed. However, the
    //visual size of canvas within browser is not modified.
    canvas.width = image.width;
    canvas.height = image.height;
}

function save_canvas_imgdata(canvas) {
    // assumes that canvas.width & canvas.height have been set to dimensions of 
    // loaded image. Will get the full image and store as window.im
    ctx = canvas.getContext('2d');
    w = canvas.width;
    h = canvas.height;
    window.im = ctx.getImageData(0, 0, w, h).data;
} 
