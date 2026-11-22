<script setup lang="ts">
import { SearchX } from 'lucide-vue-next'
import EmptyState from '@/components/common/EmptyState.vue'
import PageContainer from '@/components/common/PageContainer.vue'
import { Button } from '@/components/ui/button'
</script>

<template>
  <PageContainer>
    <EmptyState
      :icon="SearchX"
      title="Page not found"
      description="This page doesn't exist. Go back to chat."
    >
      <Button as-child variant="primary"><RouterLink to="/">Go to chat</RouterLink></Button>
    </EmptyState>
  </PageContainer>
</template>
