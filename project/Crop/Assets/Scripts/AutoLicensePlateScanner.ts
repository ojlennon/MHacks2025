import { ChatGPT, LicensePlateResponse } from "./ChatGPT";
import { CaptionBehavior } from "./CaptionBehavior";

@component
export class AutoLicensePlateScanner extends BaseScriptComponent {
  @input chatGPT: ChatGPT;
  @input text: Text;
  @input screenCropTexture: Texture; // Uses existing camera setup
  @input scanInterval: number = 2.0; // Scan every 2 seconds
  @input enableScanning: boolean = true;

  private scanTimer: DelayedCallbackEvent;
  private isScanning: boolean = false;
  private lastScanTime: number = 0;

  private plates : Map<string, LicensePlateResponse> = new Map();

  onAwake() {
    if (this.enableScanning) {
      this.startScanning();
    }
  }

  private startScanning() {
    print("Starting automatic license plate scanning...");
    this.scheduleNextScan();
  }

  private scheduleNextScan() {
    if (!this.enableScanning) return;

    this.scanTimer = this.createEvent("DelayedCallbackEvent");
    this.scanTimer.bind(() => {
      this.performScan();
    });
    this.scanTimer.reset(this.scanInterval);
  }

  private performScan() {
    this.debugImageCapture();
    if (this.isScanning) {
      print("Scan already in progress, skipping...");
      this.scheduleNextScan();
      return;
    }

    print("Performing license plate scan...");
    this.isScanning = true;

    // Send the full camera texture to the API
    this.chatGPT.makeImageRequest(
      this.screenCropTexture,
      (response: LicensePlateResponse[]) => {
        this.isScanning = false;
        
        if (response && response.length > 0) {
          for (let p of response) {
            if (!Array.from(this.plates.keys()).includes(p.plate)) {
                this.plates.set(p.plate, p);
            }
          }
        } else {
          print("No license plate detected");
        }

        this.displayResult(this.plates);
        
        // Schedule next scan
        this.scheduleNextScan();
      }
    );


  }

  private displayResult(plates: Map<string, LicensePlateResponse>) {
    // Position the caption in front of the camera
    var cameraPos = this.getSceneObject().getTransform().getWorldPosition();
    var captionPos = cameraPos.add(vec3.forward().uniformScale(-50)); // 50cm in front
    var captionRot = quat.lookAt(vec3.forward(), vec3.up());

    // Get text color based on status
    let text = "Auto-scan:\n";

    for (let [plate, value] of plates) {
        text += `${plate} - ${value.owner_name}\n`;
    }

    this.text.text = text;
  }

  private getTextColor(response: LicensePlateResponse): vec4 {
    if (response.has_warrant) {
      return new vec4(1.0, 0.2, 0.2, 1.0); // Red for warrant
    } else if (response.is_stolen) {
      return new vec4(1.0, 0.6, 0.0, 1.0); // Orange for stolen
    } else {
      return new vec4(0.2, 1.0, 0.2, 1.0); // Green for clean
    }
  }

  // Public methods to control scanning
  public startAutoScan() {
    this.enableScanning = true;
    this.startScanning();
  }

  public stopAutoScan() {
    this.enableScanning = false;
    if (this.scanTimer) {
      this.removeEvent(this.scanTimer);
    }
  }

  public setScanInterval(seconds: number) {
    this.scanInterval = seconds;
  }

  // Debug method to see what image is being sent
  public debugImageCapture() {
    Base64.encodeTextureAsync(
      this.screenCropTexture,
      (base64String) => {
        print("=== DEBUG IMAGE CAPTURE ===");
        print("Base64 length: " + base64String.length);
        print("First 100 characters: " + base64String.substring(0, 100));
        print("You can copy this base64 string and paste it in a browser with:");
        print("data:image/jpeg;base64," + base64String.substring(0, 200) + "...");
        print("=== END DEBUG ===");
      },
      () => {
        print("Debug image encoding failed!");
      },
      CompressionQuality.HighQuality,
      EncodingType.Jpg
    );
  }
}
