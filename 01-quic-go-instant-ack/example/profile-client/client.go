package main

import (
	"context"
	"crypto/tls"
	"time"

	"github.com/quic-go/quic-go"
)

const addr = "localhost:4242"

func main() {

	repetitions := 100_000
	for i := 0; i < repetitions; i++ {
		print("Client ", i)
		tlsConf := &tls.Config{
			InsecureSkipVerify: true,
			NextProtos:         []string{"quic-echo-example"},
		}
		_, _ = quic.DialAddr(context.Background(), addr, tlsConf, nil)
		time.Sleep(time.Millisecond * 100)

	}
}
