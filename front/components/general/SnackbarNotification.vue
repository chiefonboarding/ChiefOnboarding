<template>
  <v-snackbar
    v-model="show"
    :right="true"
    :timeout="6000"
    :top="true"
  >
    {{ $store.state.snackbarText }}
    <v-btn
      @click="$store.commit('setSnackbar', '')"
      color="primary"
      text
    >
      {{ $t('buttons.close') }}
    </v-btn>
  </v-snackbar>
</template>

<script>
import { mapState } from 'vuex'
export default {
  name: 'SnackbarNotification',
  data: () => ({
    show: false
  }),
  computed: mapState([
    'snackbarText',
    'snackbar'
  ]),
  watch: {
    'snackbar' (newVal) {
      this.show = newVal
    }
  }
}
</script>
