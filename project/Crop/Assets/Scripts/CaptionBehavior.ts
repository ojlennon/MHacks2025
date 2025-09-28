import animate, { CancelSet } from "SpectaclesInteractionKit.lspkg/Utils/animate";

@component
export class CaptionBehavior extends BaseScriptComponent {
  @input captionText: Text;
  @input scaleObj: SceneObject;

  private trans: Transform;
  private scaleTrans: Transform;
  private startPos: vec3;

  private scaleCancel: CancelSet = new CancelSet();
  private hideTimer: DelayedCallbackEvent;

  onAwake() {
    this.trans = this.getSceneObject().getTransform();
    this.scaleTrans = this.scaleObj.getTransform();
    this.scaleTrans.setLocalScale(vec3.zero());
  }

  openCaption(text: string, pos: vec3, rot: quat, textColor?: vec4) {
    this.startPos = pos;
    this.captionText.text = text;
    this.trans.setWorldPosition(pos);
    this.trans.setWorldRotation(rot);
    this.trans.setWorldScale(vec3.one().uniformScale(0.5));
    
    // Change text color based on license status - much simpler!
    if (textColor && this.captionText && this.captionText.textFill) {
      this.captionText.textFill.color = textColor;
    }
    
    //animate in caption
    if (this.scaleCancel) this.scaleCancel.cancel();
    animate({
      easing: "ease-out-elastic",
      duration: 1,
      update: (t: number) => {
        this.scaleTrans.setLocalScale(
          vec3.lerp(vec3.zero(), vec3.one().uniformScale(1.33), t)
        );
      },
      ended: null,
      cancelSet: this.scaleCancel,
    });
    
    // Auto-hide caption after 5 seconds
    this.scheduleHide();
  }

  private scheduleHide() {
    // Cancel any existing hide timer
    if (this.hideTimer) {
      this.removeEvent(this.hideTimer);
    }
    
    // Schedule new hide timer
    this.hideTimer = this.createEvent("DelayedCallbackEvent");
    this.hideTimer.bind(() => {
      this.hideCaption();
    });
    this.hideTimer.reset(5.0); // 5 seconds
  }

  private hideCaption() {
    if (this.scaleCancel) this.scaleCancel.cancel();
    
    animate({
      easing: "ease-in-back",
      duration: 0.5,
      update: (t: number) => {
        this.scaleTrans.setLocalScale(
          vec3.lerp(vec3.one().uniformScale(1.33), vec3.zero(), t)
        );
      },
      ended: () => {
        // Optionally disable the scene object completely
        this.getSceneObject().enabled = false;
      },
      cancelSet: this.scaleCancel,
    });
  }

  // Public method to manually hide the caption
  public hide() {
    this.hideCaption();
  }

  // Public method to cancel auto-hide (if you want to keep it visible longer)
  public cancelAutoHide() {
    if (this.hideTimer) {
      this.removeEvent(this.hideTimer);
      this.hideTimer = null;
    }
  }
}
