<template>
  <div>
    <v-row mb-4>
      <v-col sm="12">
        <h1 class="heading" style="margin-top: 5px;">
          Import (old version)
        </h1>
      </v-col>
    </v-row>
    <v-card class="mb-4 pt-2">
      <v-card-text>
       <v-textarea
          v-model="jsonData"
          label="Exported records"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn
          :loading="saving"
          @click="save"
          color="success"
        >
          Import
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'ImportPart',
  data: () => ({
    loading: false,
    saving: false,
    errors: {},
    jsonData: ''
  }),
  methods: {
    save () {
      this.saving = true
      this.$org.import(JSON.parse(this.jsonData)).then((data) => {
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
