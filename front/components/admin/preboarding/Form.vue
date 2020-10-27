<template>
  <v-container :class="{'pa-4 pt-0 grid-list-md' : !inline, 'pa-0': inline}">
    <v-row>
      <v-col sm="4">
        <v-col sm="12" class="py-0">
          <VTextFieldEmoji
            v-model="value.name"
            :label="$t('forms.title')"
            :errors="errorMessages.name"
            @removeError="errorMessages.name=''"
          />
        </v-col>
        <v-col sm="12" class="py-0">
          <TagsSelector v-model="value.tags" class="pt-2" />
        </v-col>
        <v-dialog
          v-model="dialog"
          fullscreen
          hide-overlay
          transition="dialog-bottom-transition"
          class="mt-3"
        >
          <template v-slot:activator="{ on }">
            <v-col sm="12">
              <v-btn v-on="on" color="dark" dark>
                {{ $t('preboarding.previewPage') }}
              </v-btn>
            </v-col>
          </template>
          <v-card>
            <v-toolbar dark color="dark">
              <v-btn @click="dialog = false" icon dark>
                <v-icon>close</v-icon>
              </v-btn>
              <v-toolbar-title>{{ $t('newhires.preview') }}</v-toolbar-title>
              <v-spacer />
              <v-toolbar-items>
                <v-btn @click="dialog = false" dark text>
                  Close
                </v-btn>
              </v-toolbar-items>
            </v-toolbar>
            <PreboardingPage
              :pages="[value]"
              :new-hire="$store.state.newhires.all[0]"
              :org="$store.state.org"
              disable-mustache
            />
          </v-card>
        </v-dialog>
      </v-col>
      <v-col sm="8">
        <Editor ref="editor" v-model="value.content" />
        <CustomForm v-model="value.form" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import PreboardingPage from '@/components/preboarding/Page'
export default {
  components: { PreboardingPage },
  props: {
    'value': {
      type: Object,
      required: true
    },
    'errors': {
      type: Object,
      required: true
    },
    'inline': {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    dialog: false,
    search: ''
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
    errors (value) {
      if ('content' in value) {
        this.$store.dispatch('showSnackbar', 'Content: ' + value.content[0])
      }
    }
  }
}
</script>
