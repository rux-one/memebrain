import { AutoProcessor, AutoModelForCausalLM, RawImage } from '@huggingface/transformers';

class ImageService {
  private modelId = 'vikhyatk/moondream2';
  private model: any = null;
  private processor: any = null;

  async initialize() {
    if (this.model && this.processor) return;

    console.log('Initializing Moondream2 model...');
    // @ts-ignore
    this.model = await AutoModelForCausalLM.from_pretrained(this.modelId, {
      dtype: 'q8', // Use fp32 or q8 for CPU
      device: 'cpu', 
    });
    
    // @ts-ignore
    this.processor = await AutoProcessor.from_pretrained(this.modelId, {
      trust_remote_code: true,
    });
    console.log('Moondream2 model initialized.');
  }

  async generateCaption(imagePath: string): Promise<void> {
    try {
      if (!this.model || !this.processor) {
        await this.initialize();
      }

      console.log(`Generating caption for ${imagePath}...`);
      const image = await RawImage.read(imagePath);
      console.log('RawImage loaded:', image);

      const inputs = await this.processor.caption(image, "short", {
        max_new_tokens: 768,
        emperature: 0.25,
        do_sample: true,
        top_p: 0.3,
      });
      
      console.log(123, inputs);
      
    } catch (error) {
      console.error('Error generating caption:', error);
    }
  }
}

export const imageService = new ImageService();
