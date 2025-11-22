<template>
  <div class="flex flex-col items-center justify-center h-[80vh]">
    <div class="w-full max-w-lg p-8 bg-gray-800 rounded-xl border border-dashed border-gray-600 hover:border-gray-400 transition-colors cursor-pointer relative" @click="triggerFileInput">
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        class="hidden"
        @change="handleFileChange"
      />
      <div v-if="!uploading && !success" class="text-center">
        <p class="text-xl mb-2">Click or Drag to Upload Meme</p>
        <p class="text-sm text-gray-400">Supports JPG, PNG, WEBP</p>
      </div>
      <div v-else-if="uploading" class="text-center text-blue-400">
        Uploading...
      </div>
      <div v-else-if="success" class="text-center text-green-400">
        <p class="text-xl">Upload Successful!</p>
        <button @click.stop="reset" class="mt-4 text-sm underline text-gray-400 hover:text-white">Upload another</button>
      </div>
      <div v-if="error" class="mt-4 text-center text-red-400">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const fileInput = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const success = ref(false);
const error = ref('');

function triggerFileInput() {
  if (!uploading.value) {
    fileInput.value?.click();
  }
}

function reset() {
  success.value = false;
  error.value = '';
  if (fileInput.value) fileInput.value.value = '';
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  
  if (!file) return;

  uploading.value = true;
  error.value = '';
  
  const formData = new FormData();
  formData.append('image', file);

  try {
    const res = await fetch('http://localhost:3000/api/meme/upload', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      throw new Error('Upload failed');
    }
    
    success.value = true;
  } catch (err) {
    console.error(err);
    error.value = 'Failed to upload image';
  } finally {
    uploading.value = false;
  }
}
</script>
