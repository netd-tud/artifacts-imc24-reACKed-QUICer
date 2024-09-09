package main

import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"encoding/pem"
	"log"
	"math/big"
	"os"
	"runtime/pprof"
	"sync"
	"time"

	"github.com/quic-go/quic-go"
)

const addr = "localhost:4242"

func main() {
	f, err := os.Create("cpu.prof")
	if err != nil {
		log.Fatal("could not create CPU profile: ", err)
	}
	defer f.Close()

	if err := pprof.StartCPUProfile(f); err != nil {
		log.Fatal("Could not start CPU profile ", err)
	}
	defer pprof.StopCPUProfile()

	repetitions := 100_000
	wg := sync.WaitGroup{}
	wg.Add(1)
	go func() {
		pprof.Do(context.Background(), pprof.Labels("server", "server"), func(ctx context.Context) {
			echoServer(repetitions)
		})
		wg.Done()
	}()

	wg.Wait()
}

// Start a server that echos all data on the first stream opened by the client
func echoServer(repetitions int) error {
	listener, err := quic.ListenAddr(addr, generateTLSConfig(), &quic.Config{
		EnableFirstPacketDelay: 0 * time.Millisecond,
	})
	if err != nil {
		return err
	}
	// Close immediately after handshake
	if err != nil {
		return err
	}
	for i := 0; i < repetitions; i++ {
		conn, err := listener.Accept(context.Background())
		if err != nil {
			return err
		}

		conn.CloseWithError(0, "")
	}
	return nil

}

// Setup a bare-bones TLS config for the server
func generateTLSConfig() *tls.Config {
	key, err := rsa.GenerateKey(rand.Reader, 1024)
	if err != nil {
		panic(err)
	}
	template := x509.Certificate{SerialNumber: big.NewInt(1)}
	certDER, err := x509.CreateCertificate(rand.Reader, &template, &template, &key.PublicKey, key)
	if err != nil {
		panic(err)
	}
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY", Bytes: x509.MarshalPKCS1PrivateKey(key)})
	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: certDER})

	tlsCert, err := tls.X509KeyPair(certPEM, keyPEM)
	if err != nil {
		panic(err)
	}
	return &tls.Config{
		Certificates: []tls.Certificate{tlsCert},
		NextProtos:   []string{"quic-echo-example"},
	}
}
