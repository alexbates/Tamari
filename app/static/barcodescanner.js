// Start the barcode scanner using QuaggaJS
function startScanner() {
    Quagga.init({
      inputStream: {
        name: "Live",
        type: "LiveStream",
        target: document.querySelector('#scanner-container'),
        constraints: {
          facingMode: "environment" // Use rear camera on mobile devices
        }
      },
      decoder: {
        readers: ["upc_reader", "ean_reader", "code_128_reader"]
      }
    }, function(err) {
      if (err) {
        console.error(err);
        return;
      }
      Quagga.start();
    });

    // Listen for detected barcodes
    Quagga.onDetected(processBarcode);
  }

// Process the scanned barcode result
function processBarcode(result) {
    let code = result.codeResult.code;
    console.log("Barcode detected: " + code);
    // Stop the scanner and remove the detection callback to avoid multiple triggers
    Quagga.stop();
    Quagga.offDetected(processBarcode);
    closeModal();
    // First try UPCitemdb, then fallback to Open Food Facts if necessary
    fetchProductDetails(code);
}

// Fetch product details using UPCitemdb as primary, fallback to Open Food Facts on failure
function fetchProductDetails(upc) {
    const upcUrl = "https://api.upcitemdb.com/prod/trial/lookup?upc=" + upc;
    fetch(upcUrl)
      .then(response => response.json())
      .then(data => {
        if (data.code === "OK" && data.total > 0 && data.items && data.items.length > 0) {
          let productName = data.items[0].title || upc;
          document.getElementById("a-newitem").value = productName;
        } else {
          // Fallback to Open Food Facts API if UPCitemdb did not return a result
          fetchOpenFoodFacts(upc);
        }
      })
      .catch(error => {
        console.error("Error fetching from UPCitemdb:", error);
        // Fallback to Open Food Facts API on error
        fetchOpenFoodFacts(upc);
      });
}

// Fallback: Use Open Food Facts API to retrieve product details
function fetchOpenFoodFacts(upc) {
    const offUrl = "https://world.openfoodfacts.org/api/v0/product/" + upc + ".json";
    fetch(offUrl)
      .then(response => response.json())
      .then(data => {
        let productName = "";
        if(data.status === 1 && data.product) {
          productName = data.product.product_name || upc;
        } else {
          productName = upc;
        }
        document.getElementById("a-newitem").value = productName;
      })
      .catch(error => {
        console.error("Error fetching from Open Food Facts:", error);
        document.getElementById("a-newitem").value = upc;
      });
}

// Open the scanning modal and start the scanner
function openModal() {
    document.getElementById("barcodescanner").style.display = "block";
    startScanner();
}

// Close the modal and stop the scanner if it's still running
function closeModal() {
    document.getElementById("barcodescanner").style.display = "none";
    if (Quagga && Quagga.stop) {
      Quagga.stop();
    }
}