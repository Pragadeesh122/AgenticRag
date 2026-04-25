{{/*
Expand the name of the chart.
*/}}
{{- define "agenticrag.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "agenticrag.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Chart label value.
*/}}
{{- define "agenticrag.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "agenticrag.labels" -}}
helm.sh/chart: {{ include "agenticrag.chart" . }}
{{ include "agenticrag.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels (name + instance only).
*/}}
{{- define "agenticrag.selectorLabels" -}}
app.kubernetes.io/name: {{ include "agenticrag.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Image tag: use .Values.<component>.image.tag if set, else Chart.AppVersion.
*/}}
{{- define "agenticrag.apiImage" -}}
{{ .Values.api.image.repository }}:{{ .Values.api.image.tag | default .Chart.AppVersion }}
{{- end }}

{{- define "agenticrag.frontendImage" -}}
{{ .Values.frontend.image.repository }}:{{ .Values.frontend.image.tag | default .Chart.AppVersion }}
{{- end }}

{{/* ------------------------------------------------------------------- */}}
{{/* Conditional host/port helpers for stateful services                  */}}
{{/* ------------------------------------------------------------------- */}}

{{/*
PostgreSQL host — internal service name if enabled, else external.
*/}}
{{- define "agenticrag.dbHost" -}}
{{- if .Values.postgres.enabled }}
{{- printf "%s-postgres" (include "agenticrag.fullname" .) }}
{{- else }}
{{- .Values.postgres.external.host }}
{{- end }}
{{- end }}

{{- define "agenticrag.dbPort" -}}
{{- if .Values.postgres.enabled }}
{{- "5432" }}
{{- else }}
{{- .Values.postgres.external.port | default "5432" }}
{{- end }}
{{- end }}

{{/*
Redis host/port.
*/}}
{{- define "agenticrag.redisHost" -}}
{{- if .Values.redis.enabled }}
{{- printf "%s-redis" (include "agenticrag.fullname" .) }}
{{- else }}
{{- .Values.redis.external.host }}
{{- end }}
{{- end }}

{{- define "agenticrag.redisPort" -}}
{{- if .Values.redis.enabled }}
{{- "6379" }}
{{- else }}
{{- .Values.redis.external.port | default "6379" }}
{{- end }}
{{- end }}

{{/*
MinIO endpoint.
*/}}
{{- define "agenticrag.minioEndpoint" -}}
{{- if .Values.minio.enabled }}
{{- printf "%s-minio:9000" (include "agenticrag.fullname" .) }}
{{- else }}
{{- .Values.minio.external.endpoint }}
{{- end }}
{{- end }}

{{- define "agenticrag.minioSecure" -}}
{{- if .Values.minio.enabled }}
{{- "false" }}
{{- else }}
{{- .Values.minio.external.secure | default false | toString }}
{{- end }}
{{- end }}

{{/*
OTEL endpoint — use tempo service if monitoring enabled, else config value.
*/}}
{{- define "agenticrag.otelEndpoint" -}}
{{- if and .Values.monitoring.enabled }}
{{- printf "http://%s-tempo:4318" (include "agenticrag.fullname" .) }}
{{- else }}
{{- .Values.config.otelExporterEndpoint | default "" }}
{{- end }}
{{- end }}

{{/*
CORS allowed origins — auto-compute from ingress host if not set.
*/}}
{{- define "agenticrag.corsAllowedOrigins" -}}
{{- if .Values.config.corsAllowedOrigins }}
{{- .Values.config.corsAllowedOrigins }}
{{- else if and .Values.ingress.enabled .Values.ingress.hosts }}
{{- $host := (index .Values.ingress.hosts 0).host }}
{{- if .Values.ingress.tls }}
{{- printf "https://%s" $host }}
{{- else }}
{{- printf "http://%s" $host }}
{{- end }}
{{- else }}
{{- "http://localhost:3000" }}
{{- end }}
{{- end }}

{{/*
Frontend URL — auto-compute from ingress host.
*/}}
{{- define "agenticrag.frontendUrl" -}}
{{- if and .Values.ingress.enabled .Values.ingress.hosts }}
{{- $host := (index .Values.ingress.hosts 0).host }}
{{- if .Values.ingress.tls }}
{{- printf "https://%s" $host }}
{{- else }}
{{- printf "http://%s" $host }}
{{- end }}
{{- else }}
{{- "http://localhost:3000" }}
{{- end }}
{{- end }}

{{/*
Secret name — pre-existing or chart-managed.
*/}}
{{- define "agenticrag.secretName" -}}
{{- if .Values.secrets.externalSecret }}
{{- .Values.secrets.secretName }}
{{- else }}
{{- printf "%s-secrets" (include "agenticrag.fullname" .) }}
{{- end }}
{{- end }}

{{/*
ConfigMap name.
*/}}
{{- define "agenticrag.configMapName" -}}
{{- printf "%s-config" (include "agenticrag.fullname" .) }}
{{- end }}
