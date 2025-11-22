<template>
  <div class="min-h-screen flex flex-col">
    <nav class="p-4 border-b border-gray-800 flex gap-4 justify-center">
      <router-link to="/" class="hover:text-gray-400">Home</router-link>
      <router-link to="/upload" class="hover:text-gray-400">Upload</router-link>
    </nav>
    <main class="flex-1 p-4">
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
</script>
