FROM golang:1.24.8-alpine AS build

ARG TARGETARCH

RUN CGO_ENABLED=0 GOOS=linux GOARCH=${TARGETARCH} GOBIN=/out \
    go install github.com/minio/minio@RELEASE.2025-10-15T17-29-55Z \
    && test -s /out/minio

FROM alpine:3.22

RUN apk add --no-cache ca-certificates
COPY --from=build /out/minio /usr/local/bin/minio
RUN /usr/local/bin/minio --version

ENTRYPOINT ["/usr/local/bin/minio"]