<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="900"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('intro.item') }}
      </v-card-title>

      <v-card-text>
        <IntroForm v-model="tempIntro" :errors="errors" :inline="true" />
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
import IntroForm from '@/components/admin/intro/Form'
export default {
  name: 'IntroModal',
  components: { IntroForm },
  props: {
    intro: {
      type: Object,
      required: true
    },
    value: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    loading: false,
    nameError: [],
    errors: {},
    tempIntro: { name: '', intro_person: '', tags: [] }
  }),
  watch: {
    value (value) {
      if (Object.entries(this.intro).length === 0) {
        this.tempIntro = { name: '', intro_person: '', tags: [] }
      } else {
        this.tempIntro = JSON.parse(JSON.stringify(this.intro))
      }
    }
  },
  methods: {
    addTodo () {
      if (this.tempIntro.name === '') {
        this.errors = { 'name': ['This field is required'] }
        return
      }
      let remove = -1
      if (JSON.stringify(this.tempIntro) !== JSON.stringify(this.intro)) {
        if ('id' in this.tempIntro) {
          remove = this.tempIntro.task_id
          delete this.tempIntro.id
        }
        this.tempIntro.template = false
        this.loading = true
        this.$intros.create(this.tempIntro).then((data) => {
          data.type = 'intro'
          this.$emit('change', { 'add': data, remove })
          this.$emit('input', false)
        }).catch((error) => {
          this.errors = error
          this.$store.dispatch('showSnackbar', this.$t('intro.couldNotSave'))
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
