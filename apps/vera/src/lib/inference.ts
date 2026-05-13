// apps/vera/src/lib/inference.ts
import * as tf from '@tensorflow/tfjs'
import '@tensorflow/tfjs-backend-webgl'

// DISCLAIMER: VERA is a screening tool only — not a clinical diagnostic.
// Every result must be confirmed by a qualified health worker.

export const DISEASE_CLASSES = [
  'Cutaneous Leishmaniasis',
  'Tinea Corporis',
  'Scabies',
  'Impetigo',
  'Cellulitis',
  'Melanocytic Nevi',
  'Seborrheic Keratosis',
  'Basal Cell Carcinoma',
] as const

export const TREATMENT_PROTOCOLS: Record<string, string> = {
  'Cutaneous Leishmaniasis': 'Miltefosine 2.5mg/kg/day · 28 days · Refer specialist',
  'Tinea Corporis':          'Clotrimazole 1% topical · 2–4 weeks',
  'Scabies':                 'Permethrin 5% cream · Single application · Treat contacts',
  'Impetigo':                'Mupirocin 2% topical · 5–7 days OR Amoxicillin oral',
  'Cellulitis':              'Amoxicillin-Clavulanate 500mg · 5–7 days · Refer if spreading',
  'Melanocytic Nevi':        'Benign — monitor for changes. Refer dermatology if ABCDE+',
  'Seborrheic Keratosis':    'Benign — no treatment required. Reassure patient.',
  'Basal Cell Carcinoma':    'URGENT: Refer dermatology/oncology immediately.',
}

const IMG_SIZE = 224
const IMAGENET_MEAN = [0.485, 0.456, 0.406]
const IMAGENET_STD  = [0.229, 0.224, 0.225]

let model: tf.GraphModel | null = null

export async function initTF(): Promise<string> {
  await tf.setBackend('webgl')
  await tf.ready()
  return tf.getBackend()
}

export async function loadModel(modelUrl: string): Promise<void> {
  model = await tf.loadGraphModel(modelUrl)
  // Warmup — first inference is always slow
  const dummy = tf.zeros([1, IMG_SIZE, IMG_SIZE, 3])
  model.predict(dummy)
  dummy.dispose()
}

export function isModelLoaded(): boolean {
  return model !== null
}

export interface InferenceResult {
  label: string
  confidence: number
  treatment: string
  latencyMs: number
}

export async function runInference(
  videoEl: HTMLVideoElement
): Promise<InferenceResult> {
  if (!model) throw new Error('Model not loaded')

  const t0 = performance.now()

  const result = tf.tidy(() => {
    // Capture frame → resize → normalize
    const raw = tf.browser.fromPixels(videoEl)           // [H, W, 3]
    const resized = tf.image.resizeBilinear(raw, [IMG_SIZE, IMG_SIZE]) // [224,224,3]
    const float = resized.toFloat().div(255.0)           // [0, 1]

    // ImageNet normalisation
    const mean = tf.tensor([IMAGENET_MEAN])
    const std  = tf.tensor([IMAGENET_STD])
    const normalised = float.sub(mean).div(std)          // [-~3, ~3]

    const batched = normalised.expandDims(0)             // [1,224,224,3]
    const logits  = model!.predict(batched) as tf.Tensor
    const probs   = tf.softmax(logits)
    return probs.dataSync()
  })

  const latencyMs = performance.now() - t0
  const topIdx    = Array.from(result).indexOf(Math.max(...Array.from(result)))
  const label     = DISEASE_CLASSES[topIdx]

  return {
    label,
    confidence: Math.round(result[topIdx] * 100),
    treatment:  TREATMENT_PROTOCOLS[label] ?? 'Refer to qualified health worker',
    latencyMs:  Math.round(latencyMs),
  }
}