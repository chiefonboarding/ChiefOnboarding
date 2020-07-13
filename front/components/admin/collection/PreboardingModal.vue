<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="900"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('preboarding.item') }}
      </v-card-title>

      <v-card-text>
        <PreboardingForm ref="form" v-model="tempPreboarding" :errors="errors" :inline="true" />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          @click="$emit('input', false)"
          text
        >
          {{ $t('buttons.cancel') }}
        </v-btn>
        <v-btn
          :loading="loading"
          @click="addTodo"
        >
          {{ $t('buttons.add') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import PreboardingForm from '@/components/admin/preboarding/Form'
export default {
  name: 'PreboardingModal',
  components: { PreboardingForm },
  props: {
    preboarding: {
      type: Object,
      default: () => { return {} }
    },
    value: Boolean
  },
  data: () => ({
    loading: false,
    nameError: [],
    errors: {},
    tempPreboarding: { name: '', data: [], when: '', content: '', tags: [], early_files: [] }
  }),
  watch: {
    value (value) {
      if (Object.entries(this.preboarding).length === 0) {
        this.tempPreboarding = { name: '', data: [], when: '', content: '', tags: [], early_files: [] }
      } else {
        this.tempPreboarding = JSON.parse(JSON.stringify(this.preboarding))
      }
    }
  },
  methods: {
    addTodo () {
      if (this.tempPreboarding.name === '' || this.tempPreboarding.message === '') {
        if (this.tempPreboarding.name === '') {
          this.nameError = [this.$t('forms.errors.fieldRequired')]
        }
        if (this.tempPreboarding.message === '') {
          this.$store.dispatch('showSnackbar', this.$t('forms.errors.content'))
        }
        return
      }
      let remove = -1
      if (JSON.stringify(this.tempPreboarding) !== JSON.stringify(this.preboarding)) {
        if ('id' in this.tempPreboarding) {
          remove = this.tempPreboarding.task_id
          delete this.tempPreboarding.id
        }
        this.tempPreboarding.template = false
        this.loading = true
        this.$preboarding.create(this.tempPreboarding).then((data) => {
          data.type = 'todo'
          this.$emit('change', { 'add': data, remove })
          this.$emit('input', false)
        }).catch((error) => {
          if (error) {
            this.$store.dispatch('showSnackbar', this.$t('preboarding.couldNotSave'))
          }
        }).finally(() => {
          this.loading = false
        })
      } else {
        this.$emit('input', false)
      }
    }
  }
}
</script>
