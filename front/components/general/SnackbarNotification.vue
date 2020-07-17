<template>
  <v-snackbar
    v-model="show"
    :right="true"
    :timeout="6000"
    :top="true"
  >
    {{ $store.state.snackbarText }}
    <template v-slot:action="{ attrs }">
      <v-btn
        @click="$store.commit('setSnackbar', '')"
        v-bind="attrs"
        color="primary"
        text
      >
        {{ $t('buttons.close') }}
      </v-btn>
    </template>
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
