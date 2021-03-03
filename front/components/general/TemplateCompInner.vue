<template>
  <v-col xs="12" mb="8" offset-mb="2" sm="10" offset-sm="1">
    <div>
      <v-row class="mb-4">
        <v-col sm="6">
          <slot name="header" />
        </v-col>
        <v-col sm="6" style="text-align:right; padding-top:18px; margin-top: 12px;">
          <slot name="header-right" />
        </v-col>
      </v-row>
      <v-container class="md pa-0">
        <v-card>
          <slot name="formpart" />
          <v-row class="ma-0">
            <v-col xs="12">
              <slot name="footer" />
            </v-col>
          </v-row>
        </v-card>
      </v-container>
    </div>
  </v-col>
</template>

<script>
export default {
  layout: 'admin'
}
</script>
