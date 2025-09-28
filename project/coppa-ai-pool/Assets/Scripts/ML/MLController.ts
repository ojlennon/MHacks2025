import { CameraService } from "../CameraService";
import { DetectionController } from "./DetectionController";
import { DetectionHelpers } from "./DetectionHelpers";
// import { PoolTablePredictor } from "../PoolTablePredictor"; // Not needed for license plates

type GridEntry = [number, number];

@component
export class MLController extends BaseScriptComponent {
  @input() cameraService: CameraService;
  // @input() poolTablePredictor: PoolTablePredictor; // Not needed for license plates
  @input() model: MLAsset;
  @input() modelInfo: boolean;

  @input()
  @widget(new SliderWidget(0, 1, 0.01))
  scoreThreshold: number = 0.1; // Lowered for license plate detection

  @input()
  @widget(new SliderWidget(0, 1, 0.01))
  iouThreshold: number = 0.5;

  private grids: GridEntry[][][] = [];
  private boxes: [number, number, number, number][] = [];
  private scores: { cls: number; score: number }[] = [];
  private inputShape: vec3;
  private mlComponent: MLComponent;
  private outputs: OutputPlaceholder[];
  private inputs: InputPlaceholder[];
  private isRunning: boolean = false;

  @input()
  detectionController: DetectionController;

  // COCO classes - we'll focus on vehicles that have license plates
  private classSettings: { label: string; enabled: boolean }[] = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
    "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed",
    "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven",
    "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
  ].map((label, index) => ({ 
    label: label, 
    enabled: index === 2 || index === 5 || index === 7 // Only enable car, bus, truck
  }));

  private classCount: number = 80; // COCO has 80 classes

  private anchors: number[][][] = [
    [
      [19, 27],
      [44, 40],
      [38, 94]
    ],
    [
      [96, 68],
      [86, 152],
      [180, 137]
    ],
    [
      [140, 301],
      [303, 264],
      [238, 542]
    ],
  ];

  private strides: number[] = [8, 16, 32];

  private currentFrame: number = 0;

  private runTimeStamp: number = 0;
  onAwake() {
    this.classCount = this.classSettings.length;
  }

  /**
   * create ml component
   */
  public init() {
    if (!this.model) {
      print("Error, please set ML Model asset input");
      return;
    }

    this.cameraService.saveMatrix();

    this.mlComponent = this.getSceneObject().createComponent("MLComponent");
    this.mlComponent.model = this.model;
    this.mlComponent.onLoadingFinished = this.onLoadingFinished.bind(this);
    this.mlComponent.inferenceMode = MachineLearning.InferenceMode.Accelerator;
    this.mlComponent.build([]);
  }

  /**
   * configures inputs and outputs, starts running ml component
   */
  private onLoadingFinished() {
    this.outputs = this.mlComponent.getOutputs();
    this.inputs = this.mlComponent.getInputs();

    this.printInfo("Model built");
    print("[LOG] Model loaded - Inputs: " + this.inputs.length + ", Outputs: " + this.outputs.length);
    
    // build grids
    for (let i = 0; i < this.outputs.length; i++) {
      const shape = this.outputs[i].shape;
      print("[LOG] Output " + i + " shape: " + shape.x + "x" + shape.y + "x" + shape.z);
      this.grids.push(this.makeGrid(shape.x, shape.y));
    }
    this.inputShape = this.inputs[0].shape;
    print("[LOG] Input shape: " + this.inputShape.x + "x" + this.inputShape.y + "x" + this.inputShape.z);
    print("[LOG] Class count: " + this.classCount + ", Score threshold: " + this.scoreThreshold);
    this.inputs[0].texture = this.cameraService.screenCropTexture;
    // run on update
    //this.mlComponent.runScheduled(true, MachineLearning.FrameTiming.Update, MachineLearning.FrameTiming.Update);

    this.mlComponent.onRunningFinished = this.onRunningFinished.bind(this);

    // process outputs on script update (after ml update)
    this.cameraService.frameCallback = this.onUpdate.bind(this);
  }

  /**
   *
   * @param nx
   * @param ny
   * @returns
   */
  private makeGrid(nx: number, ny: number): GridEntry[][] {
    const grids: GridEntry[][] = [];
    for (let dy = 0; dy < ny; dy++) {
      const grid: GridEntry[] = [];
      for (let dx = 0; dx < nx; dx++) {
        grid.push([dx, dy]);
      }
      grids.push(grid);
    }
    return grids;
  }

  
  /**
   * process outputs on each update
   */
  private onUpdate(runTimeStamp: number) {
    let frameSkip = 0; // No table alignment needed for license plates
    if (!this.isRunning) this.currentFrame++;
    if (this.currentFrame >= frameSkip && !this.isRunning) {
      this.currentFrame = 0;
      this.isRunning = true;
      
      print("[LOG] Running ML inference at timestamp: " + runTimeStamp);
      this.runTimeStamp =  runTimeStamp;
      let runImmediate = this.cameraService.isEditor || global.scene.isRecording();
      if (runImmediate) {
        this.cameraService.saveMatrix();
      } else {
        this.cameraService.saveMatrixWithPose(
          this.cameraService.estimateCameraPose(this.runTimeStamp)
        );
      } 

      if (this.cameraService.isEditor) {
        let delay = this.createEvent("DelayedCallbackEvent")
        delay.bind(() => {
          this.mlComponent.runImmediate(runImmediate);
        });
        delay.reset(0.01);
      } else {
        this.mlComponent.runImmediate(runImmediate);
      }
      
    }
  }

  private onRunningFinished() {
    this.parseYolo7Outputs(this.outputs);

    print("[LOG] ML finished - Raw detections: " + this.boxes.length + " boxes, " + this.scores.length + " scores");

    let result = DetectionHelpers.nms(
      this.boxes,
      this.scores,
      this.scoreThreshold,
      this.iouThreshold
    ).sort(DetectionHelpers.compareByScoreReversed);

    print("[LOG] After NMS: " + result.length + " detections (threshold: " + this.scoreThreshold + ")");

    for (let i = 0; i < result.length; i++) {
      if (
        this.classSettings.length > result[i].index &&
        this.classSettings[result[i].index].label
      ) {
        result[i].label = this.classSettings[result[i].index].label;
        print("[LOG] Detection " + i + ": class=" + result[i].index + " (" + result[i].label + "), confidence=" + result[i].score.toFixed(3));
      }
    }

    let detectionsEnabled = this.detectionController.getSceneObject().getParent().enabled;
    this.detectionController.debugImage.getSceneObject().enabled = detectionsEnabled;
    if (detectionsEnabled) {
      this.detectionController.onUpdate(result);
    }

    // No pool table predictor needed for license plates
    // TODO: Add license plate text extraction here
    

    this.isRunning = false;
  }

  /**
   * @param msg
   */
  private printInfo(msg: string) {
    if (this.modelInfo) {
      print(msg);
    }
  }

  /**
   *
   * @param outputs
   * @returns
   */
  private parseYolo7Outputs(
    outputs: OutputPlaceholder[]
  ): [number[][], { cls: number; score: number }[]] {
    this.boxes = [];
    this.scores = [];
    const num_heads = outputs.length;
    print("[LOG] Parsing YOLO outputs - " + num_heads + " heads, " + this.classCount + " classes");
    let totalDetections = 0;
    for (let i = 0; i < num_heads; i++) {
      const output = outputs[i];
      const data = output.data;
      const shape = output.shape;
      const nx = shape.x;
      const ny = shape.y;
      const step = this.classCount + 4 + 1;

      // [nx, ny, 255] -> [nx, ny, n_anchors(3), n_outputs(classCount + 4 + 1)]
      for (let dy = 0; dy < ny; dy++) {
        for (let dx = 0; dx < nx; dx++) {
          for (let da = 0; da < this.anchors.length; da++) {
            const idx =
              dy * nx * this.anchors.length * step +
              dx * this.anchors.length * step +
              da * step;
            // 0-1: xy, 2-3: wh, 4: conf, 5-5+classCount: scores
            let x = data[idx];
            let y = data[idx + 1];
            let w = data[idx + 2];
            let h = data[idx + 3];
            let conf = data[idx + 4];

            if (conf > this.scoreThreshold) {
              // print("[DEBUG] YOLO Parse - Found detection with conf: " + conf);
              x = (x * 2 - 0.5 + this.grids[i][dy][dx][0]) * this.strides[i];
              y = (y * 2 - 0.5 + this.grids[i][dy][dx][1]) * this.strides[i];
              w = w * w * this.anchors[i][da][0];
              h = h * h * this.anchors[i][da][1];

              const res = { cls: 0, score: 0 };
              const box = [
                x / this.inputShape.x,
                y / this.inputShape.y,
                w / this.inputShape.y,
                h / this.inputShape.y,
              ];
              for (let nc = 0; nc < this.classCount; nc++) {
                if (!this.classSettings[nc].enabled) {
                  continue;
                }
                const class_score = data[idx + 5 + nc] * conf;
                if (
                  class_score > this.scoreThreshold &&
                  class_score > res.score
                ) {
                  res.cls = nc;
                  res.score = class_score;
                }
              }
              if (res.score > 0) {
                this.boxes.push(box as [number, number, number, number]);
                this.scores.push(res);
                totalDetections++;
              }
            }
          }
        }
      }
    }
    print("[LOG] Parse complete - Found " + totalDetections + " raw detections above threshold " + this.scoreThreshold);
    print("[LOG] Enabled classes: car(" + this.classSettings[2].enabled + "), bus(" + this.classSettings[5].enabled + "), truck(" + this.classSettings[7].enabled + ")");
    return [this.boxes, this.scores];
  }


  /**
   * returns a number of classes that model detects
   * @returns
   */
  private getClassCount(): number {
    return this.classCount;
  }

  private getClassLabel(index: number): string {
    return this.classSettings[index].label
      ? this.classSettings[index].label
      : "class_" + index;
  }

  private setClassEnabled(index: number, value: boolean) {
    this.classSettings[index].enabled = value;
  }

  private getClassEnabled(index: number): boolean {
    return this.classSettings[index].enabled;
  }
}