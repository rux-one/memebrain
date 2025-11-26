<template>
  <div class="flex flex-col items-center justify-center min-h-[80vh]">
    <Logo class="text-purple-500 mb-8" width="16rem" height="16rem" />
    <div class="w-full max-w-2xl">
      <input
        ref="searchInput"
        v-model="query"
        type="text"
        placeholder="Search memes..."
        class="w-full bg-gray-800 border border-gray-700 rounded-lg px-6 py-4 text-xl focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
        @input="handleSearchInput"
      />
      
      <div class="flex items-center mt-4 bg-gray-800 border border-gray-700 rounded-lg px-6 py-3">
        <span class="text-gray-400 text-sm mr-4 min-w-[100px]">Similarity: {{ threshold }}</span>
        <input 
          type="range" 
          v-model.number="threshold" 
          min="0" 
          max="1" 
          step="0.05"
          class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          @input="handleSearchInput"
        />
      </div>
      
      <!-- Search results -->
      <div v-if="searchResults.length > 0" class="mt-6">
        <div class="text-center text-gray-400 mb-4">
          Found {{ searchResults.length }} results
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div 
            v-for="result in searchResults" 
            :key="result.id"
            class="bg-gray-800 rounded-lg overflow-hidden hover:bg-gray-700 transition-colors"
          >
            <img 
              :src="`/api/meme/image/${result.filename}`"
              :alt="result.caption"
              class="w-full h-48 object-cover cursor-pointer"
              @click="selectImage(result)"
              @error="handleImageError"
            />
            <div class="p-3">
              <div class="text-sm text-gray-300 mb-1">{{ result.caption }}</div>
              <div class="text-xs text-gray-500">Score: {{ result.score.toFixed(3) }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Status messages -->
      <div v-else-if="hasSearched && query.trim()" class="mt-4 text-center text-gray-500">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import Logo from '../components/Logo.vue';

interface SearchResult {
  id: string;
  score: number;
  filename: string;
  caption: string;
}

const query = ref('');
const threshold = ref(0.15);
const message = ref('');
const hasSearched = ref(false);
const searchResults = ref<SearchResult[]>([]);
const searchInput = ref<HTMLInputElement | null>(null);
let searchTimeout: ReturnType<typeof setTimeout> | null = null;

onMounted(() => {
  searchInput.value?.focus();
  window.addEventListener('keydown', handleGlobalKeydown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown);
});

function handleGlobalKeydown(event: KeyboardEvent) {
  // Don't trigger if we're already in an input or textarea (unless it's just the body)
  const target = event.target as HTMLElement;
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
    return;
  }

  // Don't trigger for special keys (Ctrl, Alt, etc)
  if (event.ctrlKey || event.altKey || event.metaKey) {
    return;
  }

  // Focus search input
  searchInput.value?.focus();
}

async function performSearch(searchQuery: string) {
  if (!searchQuery.trim()) {
    searchResults.value = [];
    hasSearched.value = false;
    return;
  }
  
  try {
    const res = await fetch(`/api/meme/search?query=${encodeURIComponent(searchQuery)}&threshold=${threshold.value}`);
    const result = await res.json();
    
    searchResults.value = result.results || [];
    message.value = result.message;
    hasSearched.value = true;
  } catch (error) {
    console.error(error);
    message.value = 'Error searching';
    searchResults.value = [];
    hasSearched.value = true;
  }
}

function handleSearchInput() {
  // Clear existing timeout
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  
  // Debounce search with 300ms delay
  searchTimeout = setTimeout(() => {
    performSearch(query.value);
  }, 300);
}

function selectImage(result: SearchResult) {
  // Future functionality - could open modal, navigate to detail view, etc.
  console.log('Selected image:', result);
}

function handleImageError(event: Event) {
  const img = event.target as HTMLImageElement;
  // Set a placeholder or hide broken images
  img.style.display = 'none';
}
</script>
