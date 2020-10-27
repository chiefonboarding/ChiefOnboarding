<template>
  <v-container class="pa-6">
    <LoadingIcon :is-loading="loading" />
    <p v-if="items.length === 0 && !loading" class="mb-0">
      {{ $t("newhires.noFilledinForms") }}
    </p>
    <div v-for="i in items" :key="i.name" style="margin-bottom: 20px;">
      <h2 v-if="'to_do' in i" class="mb-3">
        {{ i.to_do.name }}
      </h2>
      <h2 v-else>
        {{ i.preboarding.name }}
      </h2>
      <div v-for="j in i.form" :key="j.text">
        <v-text-field
          v-if="j.type === 'input'"
          :label="j.text"
          :value="j.answer"
          disabled
        />
        <v-textarea
          v-if="j.type === 'text'"
          :label="j.text"
          :value="j.answer"
          disabled
        />
        <div v-if="j.type === 'upload' && 'value' in j">
          <label class="v-label v-label--active v-label--is-disabled theme--light" style="font-size: 12px;">{{ j.text }}</label>
          <p style="margin-bottom: 5px;">
            <a @click="downloadFile(j.value)">{{ $t("newhires.download") }} {{ j.value.name }}</a>
          </p>
        </div>
        <div v-if="j.type === 'check'">
          <label class="v-label v-label--active v-label--is-disabled theme--light" style="font-size: 12px;">{{ j.text }}</label>
          <div v-for="h in j.items" :key="h.value">
            <v-checkbox
              v-model="h.value"
              :label="h.name"
              disabled
              style="margin-top: 0px;"
            />
          </div>
        </div>
        <div v-if="j.type === 'select'">
          <v-radio-group v-model="j.answer" :label="j.text">
            <v-radio
              v-for="(h, index) in j.options"
              :key="index"
              :label="h.name"
              :value="h.name"
              disabled
            />
          </v-radio-group>
        </div>
      </div>
    </div>
  </v-container>
</template>

<script>
export default {
  data: () => ({
    items: [],
    loading: true
  }),
  mounted () {
    this.$newhires.getFilledInForms(this.$route.params.id).then((items) => {
      this.items = items.filter(a => a.form.length)
    }).finally(() => {
      this.loading = false
    })
  },
  methods: {
    downloadFile (item) {
      this.$newhires.downloadFile(item.id, item.uuid).then((data) => {
        window.open(data.url, '_blank').focus()
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.couldNotGetFile'))
      })
    }
  }
}
</script>
