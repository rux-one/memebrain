<template>
  <div 
    class="logo-mask inline-block"
    :style="{
      maskImage: `url(${logoUrl})`,
      WebkitMaskImage: `url(${logoUrl})`,
      maskSize: 'contain',
      WebkitMaskSize: 'contain',
      maskRepeat: 'no-repeat',
      WebkitMaskRepeat: 'no-repeat',
      maskPosition: 'center',
      WebkitMaskPosition: 'center',
      backgroundColor: 'currentColor',
      width: width,
      height: height
    }"
  ></div>
</template>

<script setup lang="ts">
import logoUrl from '../assets/memebrain_logo.svg'

withDefaults(defineProps<{
  width?: string
  height?: string
}>(), {
  width: '2rem',
  height: '2rem'
})
</script>

<style scoped>
.logo-mask {
  /* Default fallback size if props fail or for debugging */
  min-width: 1rem;
  min-height: 1rem;
}
</style>
