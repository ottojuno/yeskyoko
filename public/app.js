const uploadInput = document.querySelector("#upload");
const uploadButton = document.querySelector(`#uploadButton`);
const adDiv = document.querySelector("#ad");
const previewCanvas = document.querySelector("#preview");
const responseDiv = document.querySelector("#response");
const spinnerDiv = document.querySelector("#spinner");
const messageDiv = document.querySelector("#message");

const ctx = previewCanvas.getContext("2d");

let DidUserHitPlay = false;
const YesKyokoThreshold = 0.7;

// from: https://stackoverflow.com/questions/7584794/accessing-jpeg-exif-rotation-data-in-javascript-on-the-client-side
// -1 = not defined, 1/2 = 0, 3/4 = 180, 5/6 = -90, 7/8 = 90
function getOrientation(file, callback) {
  var reader = new FileReader();
  reader.onload = function(e) {
    var view = new DataView(e.target.result);
    if (view.getUint16(0, false) != 0xffd8) {
      return callback(-2);
    }
    var length = view.byteLength,
      offset = 2;
    while (offset < length) {
      if (view.getUint16(offset + 2, false) <= 8) return callback(-1);
      var marker = view.getUint16(offset, false);
      offset += 2;
      if (marker == 0xffe1) {
        if (view.getUint32((offset += 2), false) != 0x45786966) {
          return callback(-1);
        }

        var little = view.getUint16((offset += 6), false) == 0x4949;
        offset += view.getUint32(offset + 4, little);
        var tags = view.getUint16(offset, little);
        offset += 2;
        for (var i = 0; i < tags; i++) {
          if (view.getUint16(offset + i * 12, little) == 0x0112) {
            return callback(view.getUint16(offset + i * 12 + 8, little));
          }
        }
      } else if ((marker & 0xff00) != 0xff00) {
        break;
      } else {
        offset += view.getUint16(offset, false);
      }
    }
    return callback(-1);
  };
  reader.readAsArrayBuffer(file);
}

// from: https://dev.to/nektro/createimagebitmap-polyfill-for-safari-and-edge-228
/* Safari and Edge polyfill for createImageBitmap
 * https://developer.mozilla.org/en-US/docs/Web/API/WindowOrWorkerGlobalScope/createImageBitmap
 */
if (!("createImageBitmap" in window)) {
  window.createImageBitmap = async function(blob) {
    return new Promise((resolve, reject) => {
      let img = document.createElement("img");
      img.addEventListener("load", function() {
        resolve(this);
      });
      img.src = URL.createObjectURL(blob);
    });
  };
}

const showResponse = res => {
  responseDiv.style.backgroundImage = `url("/${res}.png")`;
  responseDiv.style.display = "";
  spinnerDiv.classList.add("hide");
};

const showError = err => {
  console.error(err);
  showMessage(err);
};

const showMessage = msg => {
  responseDiv.style.display = "none";
  messageDiv.innerHTML = err;
  messageDiv.style.display = "";
};

const handle = res => {
  if (!!res.error) {
    showError(res.error);
    return;
  }

  // hide message/response while we update
  messageDiv.style.display = `none`;
  responseDiv.style.display = `none`;

  if (res.labels.length == 0) {
    // showMessage(`We could not get a clear view of a face.`);
    showMessage(`顔がよく見えません。`);
  }

  let foundKyoko = false;
  for (const label of res.labels) {
    if (label.yeskyoko >= YesKyokoThreshold) {
      showResponse("yes");
      foundKyoko = true;
    }
  }

  if (res.labels.length && !foundKyoko) showResponse("not");

  if (!DidUserHitPlay) {
    DidUserHitPlay = true;
    uploadButton.style.visibility = "hidden";
    previewCanvas.addEventListener(`click`, () => {
      uploadInput.click();
    });
    responseDiv.addEventListener(`click`, () => {
      uploadInput.click();
    });
    messageDiv.addEventListener(`click`, () => {
      uploadInput.click();
    });
  }

  messageDiv.style.display = "";

  // todo: refresh ad
};

const upload = () => {
  if (!uploadInput.files[0]) return;

  uploadButton.style.visibility = "hidden";
  messageDiv.style.display = "none";
  responseDiv.style.backgroundImage = "";
  responseDiv.style.display = "";
  spinnerDiv.classList.remove("hide");

  const file = uploadInput.files[0];

  getOrientation(file, orientation => {
    console.log(`orientation: ${orientation}`);

    let rotation = 0;
    // -1 = not defined, 1/2 = 0, 3/4 = 180, 5/6 = -90, 7/8 = 90
    switch (orientation) {
      case -1:
      case 1:
      case 2:
        rotation = 0;
        break;
      case 3:
      case 4:
        rotation = -180;
        break;
      case 5:
      case 6:
        rotation = 90;
        break;
      case 7:
      case 8:
        rotation = -90;
        break;
    }

    createImageBitmap(file).then(img => {
      const length = Math.max(img.width, img.height);
      const pivot = length * 0.5;
      const responsePosition = img.height;
      previewCanvas.width = previewCanvas.height = length;
      ctx.translate(pivot, pivot);
      ctx.rotate(rotation * Math.PI / 180);
      ctx.drawImage(img, -img.width * 0.5, -img.height * 0.5);

      // note: data must be base64 decoded serverside because of this solution.
      fetch(`/label`, {
        method: `post`,
        body: previewCanvas.toDataURL("image/jpeg", 1.0)
      })
        .then(res => res.json().then(data => handle(data)))
        .catch(err => console.log(err));
    });
  });
};

uploadInput.addEventListener(`change`, upload, false);
