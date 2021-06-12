<template>
  <div>
    <v-dialog
      v-model="value"
      :persistent="true"
      max-width="950"
      scrollable
    >
      <v-card>
        <v-card-title class="headline">
          <v-row>
            <v-col cols="6">
              <span v-if="sendVia===2">{{ $t('sequence.text') }}</span>
              <span v-if="sendVia===1">{{ $t('sequence.slack') }}</span>
              <span v-if="sendVia===0">{{ $t('sequence.emailModal') }}</span>
            </v-col>
            <v-col v-if="'id' in item && sendVia !== 2" cols="6" class="text-right">
              <v-menu bottom left>
                <template v-slot:activator="{ on }">
                  <v-btn
                    v-on="on"
                    icon
                    style="font-size: 20px"
                  >
                    <v-icon>settings</v-icon>
                  </v-btn>
                </template>

                <v-list>
                  <v-list-item
                    @click="sendTestMessage"
                  >
                    <v-list-item-title>Send test message</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </v-col>
          </v-row>
        </v-card-title>
        <v-card-text>
          <v-col sm="12" class="pa-0">
            <v-text-field
              v-model="tempItem.name"
              :label="$t('sequence.slackTitle')"
              :error-messages="errors.name[0]"
              @keyup="errors.name=[]"
            />
          </v-col>
          <v-col xs="12" class="mt-2 pa-0">
            <v-select
              v-model="tempItem.person_type"
              :items="[
                {id: 0, name: $t('sequence.newHire') },
                {id: 1, name: $t('sequence.manager')},
                {id: 2, name: $t('sequence.buddy')},
                {id: 3, name: $t('sequence.pick')}
              ]"
              :label="$t('sequence.personText')"
              item-text="name"
              item-value="id"
            />
          </v-col>
          <v-col sm="12" class="pa-0">
            <v-autocomplete
              v-if="tempItem.person_type === 3"
              v-model="tempItem.send_to"
              :items="people"
              :label="$t('sequence.employee')"
              item-value="id"
              item-text="full_name"
              class="mb-3"
            />
          </v-col>
          <v-col cols="12" class="pa-0">
            <VTextFieldEmoji
              v-if="sendVia === 0"
              v-model="tempItem.subject"
              :label="$t('sequence.subject')"
              :errors="errors.content"
              personalize
            />
          </v-col>
          <v-col sm="12" class="pa-0">
            <VTextAreaEmoji
              v-if="sendVia === 2"
              v-model="tempItem.content"
              :label="$t('sequence.textForm')"
              :errors="errors.content"
              :personalize="true"
            />
            <Editor
              v-else
              v-model="tempItem.content_json"
              :errors="errors.content_json"
              :personalize="true"
            />
          </v-col>
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
            @click="addItem()"
            :loading="loading"
          >
            <span v-if="Object.entries(item).length">
              {{ $t('buttons.update') }}
            </span>
            <span v-else>
              {{ $t('buttons.add') }}
            </span>
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
export default {
  props: {
    item: {
      type: Object,
      default: () => { return {} }
    },
    index: {
      type: Number,
      default: 0
    },
    value: {
      type: Boolean,
      default: false
    },
    sendVia: {
      // 0: email, 1: slack, 2: text
      default: 0,
      type: Number
    }
  },
  data: vm => ({
    errors: { name: [], content: [], subject: [], content_json: [] },
    loading: false,
    tempItem: {
      name: '',
      person_type: 0,
      subject: '',
      send_to: null,
      send_via: vm.sendVia,
      content: '',
      content_json: []
    }
  }),
  computed: {
    people () {
      if (this.sendVia === 1) {
        return this.$store.state.employees.all.filter(a => a.slack_user_id !== null)
      } else if (this.sendVia === 0) {
        return this.$store.state.employees.all.filter(a => a.email !== null)
      } else {
        return this.$store.state.employees.all.filter(a => a.phone !== null && a.phone !== '')
      }
    }
  },
  watch: {
    value (value) {
      if (Object.entries(this.item).length === 0) {
        this.tempItem = {
          name: '',
          person_type: 0,
          send_to: null,
          subject: '',
          send_via: this.sendVia,
          content: '',
          content_json: []
        }
      } else {
        this.tempItem = JSON.parse(JSON.stringify(this.item))
        delete this.tempItem.id
      }
      this.$store.commit('refreshEditor')
    }
  },
  methods: {
    addItem () {
      this.loading = true
      this.$sequences.createExternalMessage(this.tempItem).then((one) => {
        if ('id' in this.item) {
          this.$store.commit('sequences/removeItem', { block: this.index, id: this.item.id, type: 'external_messages' })
        }
        this.$store.commit('sequences/addItem', { block: this.index, type: 'external_messages', item: one })
        this.$emit('input', false)
      }).catch((errors) => {
        this.errors = errors
      }).finally(() => {
        this.loading = false
      })
    },
    sendTestMessage () {
      this.$sequences.sendTestMessage(this.item.id).then((data) => {
        this.$store.dispatch('showSnackbar', 'Message has been sent!')
      }).catch((error) => {
        if ('slack' in error && error.slack === 'not exist') {
          this.$store.dispatch('showSnackbar', 'Your account has not been connected to Slack yet. Go to People -> Employees -> find your profile and click on "give access"')
          return
        }
        this.$store.dispatch('showSnackbar', 'Something went wrong...')
      })
    }
  }
}
</script>

<style scoped>
</style>
