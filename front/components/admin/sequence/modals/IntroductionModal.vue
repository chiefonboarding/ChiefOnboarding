<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="1000"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('intro.item') }}
      </v-card-title>

      <v-card-text class="pa-0">
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
          @click="addIntroItem"
        >
          <span v-if="Object.entries(intro).length">
            {{ $t('buttons.update') }}
          </span>
          <span v-else>
            {{ $t('buttons.add') }}
          </span>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import IntroForm from '@/components/admin/intro/Form'
export default {
  name: 'IntroductionModal',
  components: { IntroForm },
  props: {
    intro: {
      type: Object,
      default: () => { return {} }
    },
    index: {
      type: Number,
      required: true
    },
    value: {
      type: Boolean,
      required: true
    }
  },
  data: () => ({
    loading: false,
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
    addIntroItem () {
      this.tempIntro.template = false
      this.loading = true
      delete this.tempIntro.id
      this.$intros.create(this.tempIntro).then((data) => {
        if (this.index === -1) {
          // unconditioned item
          this.$emit('updateUnconditionedItem', { id: this.intro.id || -1, type: 'introduction', item: data })
          this.$emit('input', false)
          return
        }
        if ('id' in this.intro) {
          this.$store.commit('sequences/removeItem', {
            block: this.index,
            type: 'introductions',
            id: this.intro.id
          })
        }
        this.$store.commit('sequences/addItem', { block: this.index, type: 'introductions', item: data })
        this.$emit('input', false)
      }).catch((error) => {
        this.errors = error
        this.$store.dispatch('showSnackbar', this.$t('intro.couldNotSave'))
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>
