module main

go 1.17

require github.com/apache/thrift v0.16.0
require "github.com/vishalmohanty/encryption" v0.0.0
replace "github.com/vishalmohanty/encryption" v0.0.0 => "../../thrift/gen-go/encryption"
