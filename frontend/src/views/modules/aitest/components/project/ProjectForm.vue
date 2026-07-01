<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" size="default">
    <el-form-item label="项目名称" prop="name">
      <el-input v-model="form.name" placeholder="输入项目名称" maxlength="200" />
    </el-form-item>
    <el-form-item label="项目状态" prop="status">
      <el-select v-model="form.status" style="width: 100%">
        <el-option label="活跃" value="active" />
        <el-option label="已归档" value="archived" />
      </el-select>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

export interface ProjectFormData {
  name: string
  description?: string
  status: string
}

const props = defineProps<{
  initial?: Partial<ProjectFormData>
}>()

const formRef = ref<FormInstance>()
const form = reactive<ProjectFormData>({
  name: '',
  description: '',
  status: 'active',
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 200, message: '名称长度应在 2-200 字符之间', trigger: 'blur' },
  ],
}

watch(() => props.initial, (val) => {
  if (val) {
    if (val.name !== undefined) form.name = val.name
    if (val.description !== undefined) form.description = val.description
    if (val.status !== undefined) form.status = val.status
  }
}, { immediate: true })

async function validate(): Promise<boolean> {
  const valid = await formRef.value?.validate().catch(() => false)
  return !!valid
}

function getData(): ProjectFormData {
  return { ...form }
}

defineExpose({ validate, getData })
</script>
