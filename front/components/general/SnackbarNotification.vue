<template>
  <div class="snackbars">
    <v-snackbar
      v-for="i in snackbars"
      :key="i.id"
      v-model="i.active"
      :right="true"
      :timeout="6000"
      :top="true"
      :height="30"
      :style="getMargin(i)"
    >
      {{ i.text }}
      <template v-slot:action="{ attrs }">
        <v-btn
          @click="dismissItem(i)"
          v-bind="attrs"
          color="primary"
          text
        >
          {{ $t('buttons.close') }}
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
export default {
  name: 'SnackbarNotification',
  data: () => ({
    snackbars: []
  }),
  watch: {
    '$store.state.snackbarText' (newVal) {
      let randomID = Math.random().toString(36).substr(2, 32)
      while (this.snackbars.find(a => a.id === randomID) !== undefined) {
        randomID = Math.random().toString(36).substr(2, 32)
      }
      this.snackbars.push({ text: newVal, active: true, id: randomID })
    }
  },
  methods: {
    dismissItem (item) {
      const snackbar = this.snackbars.find(a => item === a)
      snackbar.active = false
    },
    getMargin (i) {
      if (!i.active) {
        return 'display:none;'
      }
      return 'margin-top: ' + this.snackbars.filter(a => a.active).findIndex(a => a.id === i.id) * 60 + 'px'
    }
  }
}
</script>
