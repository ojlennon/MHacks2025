import { OpenAI } from "Remote Service Gateway.lspkg/HostedExternal/OpenAI";

export interface LicensePlateResponse {
  plate: string;
  owner_name: string;
  dob: string;
  has_warrant: boolean;
  registration_date: string;
  license_ex_date: string;
  warrant_reason: string;
  is_stolen: boolean;
}

@component
export class ChatGPT extends BaseScriptComponent {
  private ImageQuality = CompressionQuality.HighQuality;
  private ImageEncoding = EncodingType.Jpg;
  private internetModule:InternetModule = require("LensStudio:InternetModule");

  private url = "https://plate-ocr-production.up.railway.app/extract-base64";
  onAwake() {}

  makeImageRequest(imageTex: Texture, callback) {
    print("Making image request...");
    Base64.encodeTextureAsync(
      imageTex,
      (base64String) => {
        print("Image encode Success!");
        const textQuery =
          "Identify in as much detail what object is in the image but only use a maxiumum of 5 words";
        this.sendGPTChat(textQuery, base64String, callback);
      },
      () => {
        print("Image encoding failed!");
      },
      this.ImageQuality,
      this.ImageEncoding
    );
  }

  async sendGPTChat(
    request: string,
    image64: string,
    callback: (response: LicensePlateResponse) => void
  ) {
    print("Calling " + this.url)
    print("Sending base64 image length: " + image64.length)
    
    this.internetModule
      .fetch(this.url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          "base64_image" : image64
        })
      })
      .then((response) => {
        print("Response status: " + response.status);
        return response.json();
      })
      .then((data) => {
        print("Raw response data: " + JSON.stringify(data));
        let licensePlateResponse = data as LicensePlateResponse;
        callback(licensePlateResponse);
      })
      .catch((e) => {
          print("Network error details: " + JSON.stringify(e));
          callback(null);
        });



    // OpenAI.chatCompletions({
    //   model: "gpt-4o",
    //   messages: [
    //     {
    //       role: "user",
    //       content: [
    //         { type: "text", text: request },
    //         {
    //           type: "image_url",
    //           image_url: {
    //             url: `data:image/jpeg;base64,` + image64,
    //           },
    //         },
    //       ],
    //     },
    //   ],
    //   max_tokens: 50,
    // })
    //   .then((response) => {
    //     if (response.choices && response.choices.length > 0) {
    //       callback(response.choices[0].message.content);
    //       print("Response from OpenAI: " + response.choices[0].message.content);
    //     }
    //   })
    //   .catch((error) => {
    //     print("Error in OpenAI request: " + error);
    //   });
  }
}
