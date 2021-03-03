<template>
  <div>
    <v-row class="mb-4">
      <v-col sm="12">
        <h1 class="heading" style="margin-top: 5px;">
          Export
        </h1>
      </v-col>
    </v-row>
    <v-card class="mb-4 pt-2">
      <v-card-text>
        <v-select
          :items="items"
          v-model="item"
          label="What do you want to export?"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn
          :loading="saving"
          @click="save"
          color="success"
        >
          Export
        </v-btn>
      </v-card-actions>
    </v-card>
    <v-dialog
      v-model="dialog"
      width="500"
    >
      <v-card>
        <v-card-text class="pb-0">
          <v-textarea
            v-model="jsonData"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            @click="dialog = false"
            color="primary"
            text
          >
            {{ $t('buttons.close') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
export default {
  name: 'ExportPart',
  data: () => ({
    loading: false,
    items: [
      'preboarding', 'badges', 'to_do', 'resources', 'introductions', 'sequences', 'users', 'admin_tasks', 'appointments'
    ],
    saving: false,
    errors: {},
    jsonData: '',
    dialog: false,
    item: 'preboarding'
  }),
  methods: {
    save () {
      this.saving = true
      this.$org.export(this.item).then((data) => {
        this.jsonData = JSON.stringify(data)
        this.dialog = true
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    }
  }
}
</script>
