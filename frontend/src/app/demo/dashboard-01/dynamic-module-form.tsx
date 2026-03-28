"use client"

import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

import { Button } from "@/app/demo/dashboard-01/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/app/demo/dashboard-01/form"
import { Input } from "@/app/demo/dashboard-01/input"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/app/demo/dashboard-01/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/demo/dashboard-01/select"

// --- Metadata Mock Data (from User Request) ---
const moduleMetadata = {
  success: true,
  data: {
    module: "products",
    description: "Thực đơn",
    fields: [
      {
        name: "name",
        type: "string",
        label: "Tên sản phẩm",
        required: true,
        max_length: 255,
      },
      {
        name: "code",
        type: "string",
        label: "Mã SP",
        required: false,
        max_length: 50,
      },
      {
        name: "description",
        type: "string",
        label: "Mô tả",
        required: false,
        ui_type: "textarea",
      },
      {
        name: "price",
        type: "decimal",
        label: "Giá bán",
        required: true,
        precision: 12,
        scale: 2,
      },
      {
        name: "cost_price",
        type: "decimal",
        label: "Giá vốn",
        required: false,
        precision: 12,
        scale: 2,
      },
      {
        name: "category_id",
        type: "foreignkey",
        label: "Danh mục",
        required: true,
        to: "categories",
        display_field: "name",
      },
      {
        name: "is_available",
        type: "boolean",
        label: "Còn hàng",
        required: false,
        default: true,
      },
      {
        name: "image",
        type: "image",
        label: "Ảnh sản phẩm",
        required: false,
      },
    ],
  },
}

// --- Dynamic Schema Generator ---
function generateZodSchema(fields: any[]) {
  const shape: any = {}

  fields.forEach((field) => {
    let validator: any

    switch (field.type) {
      case "string":
        validator = z.string()
        if (field.max_length) {
          validator = validator.max(field.max_length)
        }
        if (field.required) {
          validator = validator.min(1, `${field.label} là bắt buộc`)
        } else {
          validator = validator.optional().or(z.literal(""))
        }
        break
      case "decimal":
        validator = z.coerce.number()
        if (field.required) {
          validator = validator.min(0, `${field.label} phải lớn hơn hoặc bằng 0`)
        } else {
          validator = validator.optional()
        }
        break
      case "boolean":
        validator = z.boolean()
        break
      case "foreignkey":
        validator = z.string()
        if (field.required) {
          validator = validator.min(1, `Vui lòng chọn ${field.label}`)
        }
        break
      default:
        validator = z.any().optional()
    }

    shape[field.name] = validator
  })

  return z.object(shape)
}

export function DynamicModuleForm() {
  const fields = moduleMetadata.data.fields
  const dynamicSchema = generateZodSchema(fields)

  const form = useForm({
    resolver: zodResolver(dynamicSchema),
    defaultValues: fields.reduce((acc: any, field) => {
      acc[field.name] = field.type === "boolean" ? field.default ?? false : ""
      return acc
    }, {}),
  })

  function onSubmit(values: any) {
    console.log("Form Values:", values)
    alert("Dữ liệu đã được lưu: " + JSON.stringify(values, null, 2))
  }

  return (
    <div className="rounded-xl border bg-background p-6 shadow-sm">
      <div className="mb-6 flex flex-col gap-1">
        <h2 className="text-xl font-bold tracking-tight">
          Thiết lập {moduleMetadata.data.description}
        </h2>
        <p className="text-sm text-muted-foreground">
          Giao diện tự động sinh từ Metadata Schema của hệ thống.
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {fields.map((field) => (
              <FormField
                key={field.name}
                control={form.control}
                name={field.name}
                render={({ field: formField }) => (
                  <FormItem className={field.ui_type === "textarea" ? "md:col-span-2" : ""}>
                    <FormLabel>{field.label}</FormLabel>
                    <FormControl>
                      {renderInput(field, formField)}
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            ))}
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => form.reset()}
            >
              Làm lại
            </Button>
            <Button type="submit">Lưu thay đổi</Button>
          </div>
        </form>
      </Form>
    </div>
  )
}

function renderInput(field: any, formField: any) {
  switch (field.type) {
    case "string":
      if (field.ui_type === "textarea") {
        return (
          <Textarea
            placeholder={`Nhập ${field.label}...`}
            className="min-h-32"
            {...formField}
          />
        )
      }
      return <Input placeholder={`Nhập ${field.label}...`} {...formField} />

    case "decimal":
      return (
        <Input
          type="number"
          step="0.01"
          placeholder="0.00"
          {...formField}
          onChange={(e) => formField.onChange(e.target.valueAsNumber || 0)}
        />
      )

    case "boolean":
      return (
        <div className="flex items-center space-x-2 rounded-md border p-2 bg-muted/20">
          <Checkbox
            checked={formField.value}
            onCheckedChange={formField.onChange}
          />
          <span className="text-sm font-medium leading-none">
            {field.label}
          </span>
        </div>
      )

    case "foreignkey":
      return (
        <Select
          onValueChange={formField.onChange}
          defaultValue={formField.value}
        >
          <SelectTrigger>
            <SelectValue placeholder={`Chọn ${field.label}...`} />
          </SelectTrigger>
          <SelectContent>
            {/* Mock Categories */}
            <SelectItem value="cat_1">Cà phê</SelectItem>
            <SelectItem value="cat_2">Trà trái cây</SelectItem>
            <SelectItem value="cat_3">Bánh & Snack</SelectItem>
          </SelectContent>
        </Select>
      )

    case "image":
      return (
        <div className="flex items-center gap-4">
          <div className="h-16 w-16 rounded border border-dashed flex items-center justify-center bg-muted/30">
             <span className="text-[10px] text-muted-foreground">No image</span>
          </div>
          <Input 
            type="file" 
            accept="image/*" 
            onChange={(e) => {
              // Logic xử lý file ở đây
              formField.onChange(e.target.files?.[0]?.name || "")
            }}
          />
        </div>
      )

    default:
      return <Input {...formField} />
  }
}
