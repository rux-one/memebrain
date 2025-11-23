<template>
  <div class="flex flex-col items-center justify-center h-[80vh]">
    <div class="w-full max-w-2xl">
      <input
        v-model="query"
        type="text"
        placeholder="Search memes..."
        class="w-full bg-gray-800 border border-gray-700 rounded-lg px-6 py-4 text-xl focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
        @keyup.enter="search"
      />
      <div v-if="hasSearched" class="mt-4 text-center text-gray-500">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const query = ref('');
const message = ref('');
const hasSearched = ref(false);

async function search() {
  if (!query.value.trim()) return;
  
  try {
    const res = await fetch(`/api/meme/search?query=${encodeURIComponent(query.value)}`);
    const result = await res.json();
    message.value = result.message;
    hasSearched.value = true;
  } catch (error) {
    console.error(error);
    message.value = 'Error searching';
    hasSearched.value = true;
  }
}
</script>
