<template>
  <v-row>
    <v-col cols="12" offset-mb="3" sm="8" offset-sm="2">
      <v-row class="my-4">
        <v-col cols="12">
          <h1 class="">
            {{ $t("newhires.addNew") }}
          </h1>
        </v-col>
      </v-row>
      <v-card class="mb-4 pa-6">
        <NewHireForm v-model="newHire" :errors="errors" />
        <v-autocomplete
          v-model="sequences"
          :items="$store.state.sequences.all"
          :label="$t('newhires.assignCollection')"
          chips
          item-text="name"
          item-value="id"
          multiple
          return-object
        >
          <template
            v-slot:selection="data"
          >
            <v-chip
              :input-value="data.selected"
              @click:close="remove(data.item)"
              close
              class="chip--select-multi"
            >
              {{ data.item.name }}
            </v-chip>
          </template>
          <template
            v-slot:item="data"
          >
            <template>
              <v-list-item-content v-text="data.item.name" />
            </template>
          </template>
          <template v-slot:no-data>
            <v-list-item>
              <v-list-item-content>
                <v-list-item-title>
                  Sequence couldn't be found. Check for typos.
                </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
          </template>
        </v-autocomplete>
        <v-row>
          <v-col v-if="$store.state.org.google_key" cols="6" class="py-0">
            <v-checkbox
              v-model="newHire.google.create"
              label="Create Google account"
            />
          </v-col>
          <v-col cols="6" class="py-0">
            <v-text-field
              v-if="newHire.google.create"
              v-model="newHire.google.email"
              :rules="[rules.emailMatch]"
              label="Email address"
              type="email"
              hint="The email address we will send the new email credentials to"
            />
          </v-col>
          <v-col v-if="$store.state.org.slack_account_key" cols="6" class="py-0">
            <v-checkbox
              v-model="newHire.slack.create"
              label="Create Slack account"
            />
          </v-col>
          <v-col cols="6" class="py-0">
            <v-text-field
              v-if="newHire.slack.create"
              v-model="newHire.slack.email"
              :rules="[rules.emailMatch]"
              label="Email address"
              type="email"
              hint="The email address we will send the new invite to"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-spacer />
          <v-btn :loading="createNewHireLoading" @click="createNewHire" color="primary">
            {{ $t('newhires.continue') }}
          </v-btn>
        </v-row>
      </v-card>
    </v-col>
    <SequenceModal v-model="openedModal" :items="conditionItems" :id="newHire.id" />
    <SequenceitemsNeverTriggeredModal
      v-model="neverTriggeredModal"
      :conditions="conditionItems"
      :new-hire="newHire"
      @completed="goToNewHire"
    />
  </v-row>
</template>

<script>
import moment from 'moment-timezone'
import NewHireForm from '@/components/admin/newhire/Form'
import SequenceModal from '@/components/admin/newhire/SequenceModal'
import SequenceitemsNeverTriggeredModal from '@/components/admin/sequence/modals/SequenceItemsNeverTriggeredModal'

export default {
  layout: 'admin',
  components: { SequenceitemsNeverTriggeredModal, NewHireForm, SequenceModal },
  data: vm => ({
    loading: false,
    createNewHireLoading: false,
    isAddingCollections: false,
    openedModal: false,
    rules: {
      emailMatch: v => (v.includes('@') && v.includes('.')) || 'The email you entered isn\'t valid'
    },
    neverTriggeredModal: false,
    newHire: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      position: '',

      language: vm.$store.state.org.language,
      message: '',
      start_day: moment().format('YYYY-MM-DD'),
      buddy: null,
      manager: null,
      timezone: vm.$store.state.org.timezone,
      google: {
        create: false,
        email: ''
      },
      slack: {
        create: false,
        email: ''
      }
    },
    errors: {},
    conditionItems: [],
    sequences: []
  }),
  methods: {
    createNewHire () {
      this.createNewHireLoading = true
      this.newHire.sequences = this.sequences
      this.$newhires.create(this.newHire).then((newHire) => {
        this.newHire.id = newHire.id
        this.$newhires.checkPastSequenceItems(newHire.id, this.sequences.map(a => a.id)).then((conditionItems) => {
          if (conditionItems.length) {
            this.neverTriggeredModal = true
            this.conditionItems = conditionItems
          } else {
            this.$router.push({ name: 'admin-newhire-id', params: { id: newHire.id } })
          }
        })
      }).catch((errors) => {
        this.errors = errors
      }).finally(() => {
        this.createNewHireLoading = false
      })
    },
    remove (item) {
      const index = this.sequences.indexOf(item)
      if (index >= 0) { this.sequences.splice(index, 1) }
    },
    goToNewHire () {
      this.$router.push({ name: 'admin-newhire-id', params: { id: this.newHire.id } })
    }
  }
}
</script>
