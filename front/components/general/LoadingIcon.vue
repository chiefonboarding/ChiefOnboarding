<template>
  <v-container v-if="isLoading" justify="center" style="text-align:center; flex-shrink: 0;">
    <v-progress-circular
      :color="color"
      indeterminate
    />
  </v-container>
</template>

<script>
export default {
  props: {
    isLoading: Boolean,
    color: {
      type: String,
      default: 'primary'
    }
  }
}
</script>
