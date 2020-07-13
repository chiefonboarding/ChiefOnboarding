<template>
  <v-container grid-list-md pa-4>
    <v-row>
      <v-col xs="4">
        <v-col xs="12">
          <VTextFieldEmoji
            v-model="value.name"
            :label="$t('intro.title')"
            :errors="errorMessages.name"
            @removeError="errorMessages.name=''"
          />
        </v-col>
        <v-col xs="12">
          <v-autocomplete
            v-model="value.intro_person"
            :items="$store.state.employees.all"
            :label="$t('intro.selectEmployee')"
            :error-messages="errorMessages.intro_person"
            @change="errorMessages.intro_person=''"
            item-text="full_name"
            return-object
          />
        </v-col>
        <v-col xs="12">
          <TagsSelector v-model="value.tags" class="pt-2" />
        </v-col>
      </v-col>
      <v-col xs="8" style="margin-left: 20px;">
        <div v-if="value.intro_person">
          <IntroductionItem :title="value.name" :user="value.intro_person" disable-mustache />
        </div>
        <div>
          <i style="font-size: 12px; top: 10px; position: relative">{{ text }} </i>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import IntroductionItem from '~/components/portal/IntroductionItem'
export default {
  components: { IntroductionItem },
  props: {
    value: {
      type: Object,
      default: () => { return {} }
    },
    errors: {
      type: Object,
      default: () => { return {} }
    }
  },
  data: vm => ({
    search: '',
    text: vm.$t('intro.placeholders')
  }),
  computed: {
    errorMessages () {
      return JSON.parse(JSON.stringify(this.errors))
    }
  },
  watch: {
    value: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    },
    'value.intro_person' (value) {
      this.value.intro_person_id = value.id
    },
    errors (value) {
      if ('content' in value) {
        this.$store.dispatch('showSnackbar', 'Content: ' + value.content[0])
      }
    }
  }
}
</script>
