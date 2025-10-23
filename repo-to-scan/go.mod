module github.com/example/webapp

go 1.19

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/gorilla/mux v1.8.0
    golang.org/x/text v0.11.0
    github.com/stretchr/testify v1.8.4
)

require (
    github.com/bytedance/sonic v1.9.1 // indirect
    github.com/chenzhuoyu/base64x v0.0.0-20221115062448-fe3a3abad311 // indirect
)

replace golang.org/x/text => github.com/golang/text v0.3.7