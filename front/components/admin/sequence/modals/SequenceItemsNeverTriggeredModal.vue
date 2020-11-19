<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="950"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('sequence.addRightAway') }}
      </v-card-title>

      <v-card-text>
        <div v-for="i in conditions" :key="i.id">
          <v-row>
            <v-col cols="1">
              <v-checkbox
                v-model="i.checked"
              />
            </v-col>
            <v-col class="pt-8">
              <CardLine :index="0" :removable="false" :items="i.to_do" type="to_do" />
              <CardLine :index="0" :removable="false" :items="i.resources" type="resources" />
              <CardLine :index="0" :removable="false" :items="i.badges" type="badges" />
              <CardLine :index="0" :removable="false" :items="i.admin_tasks" type="admin_tasks" />
              <CardLine :index="0" :removable="false" :items="getExternalItems(i,1)" type="slack_messages" />
              <CardLine :index="0" :removable="false" :items="getExternalItems(i,2)" type="text_messages" />
              <CardLine :index="0" :removable="false" :items="getExternalItems(i,0)" type="emails" />
            </v-col>
          </v-row>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          :loading="loading"
          @click="triggerConditions"
        >
          {{ $t('buttons.submit') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import CardLine from '../CardLine'
export default {
  name: 'SequenceitemsNeverTriggeredModal',
  components: { CardLine },
  props: {
    value: {
      type: Boolean,
      required: true
    },
    conditions: {
      type: Array,
      required: true
    },
    newHire: {
      type: Object,
      required: true
    }
  },
  data: () => ({
    loading: false
  }),
  methods: {
    getExternalItems (i, type) {
      if (!('external_messages' in i)) { return [] }
      return i.external_messages.filter(a => a.send_via === type)
    },
    triggerConditions () {
      const idArray = this.conditions.filter(a => a.checked).map(a => a.id)
      this.$newhires.triggerItems(this.newHire.id, idArray).then((data) => {
        this.$emit('input', false)
        this.$emit('completed')
        this.$store.dispatch('showSnackbar', this.$t('sequence.completedConditions'))
      })
    }
  }
}
</script>
