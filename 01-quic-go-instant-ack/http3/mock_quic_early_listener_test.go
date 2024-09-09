// Code generated by MockGen. DO NOT EDIT.
// Source: github.com/quic-go/quic-go/http3 (interfaces: QUICEarlyListener)
//
// Generated by this command:
//
//	mockgen -typed -package http3 -destination mock_quic_early_listener_test.go github.com/quic-go/quic-go/http3 QUICEarlyListener
//
// Package http3 is a generated GoMock package.
package http3

import (
	context "context"
	net "net"
	reflect "reflect"

	quic "github.com/quic-go/quic-go"
	gomock "go.uber.org/mock/gomock"
)

// MockQUICEarlyListener is a mock of QUICEarlyListener interface.
type MockQUICEarlyListener struct {
	ctrl     *gomock.Controller
	recorder *MockQUICEarlyListenerMockRecorder
}

// MockQUICEarlyListenerMockRecorder is the mock recorder for MockQUICEarlyListener.
type MockQUICEarlyListenerMockRecorder struct {
	mock *MockQUICEarlyListener
}

// NewMockQUICEarlyListener creates a new mock instance.
func NewMockQUICEarlyListener(ctrl *gomock.Controller) *MockQUICEarlyListener {
	mock := &MockQUICEarlyListener{ctrl: ctrl}
	mock.recorder = &MockQUICEarlyListenerMockRecorder{mock}
	return mock
}

// EXPECT returns an object that allows the caller to indicate expected use.
func (m *MockQUICEarlyListener) EXPECT() *MockQUICEarlyListenerMockRecorder {
	return m.recorder
}

// Accept mocks base method.
func (m *MockQUICEarlyListener) Accept(arg0 context.Context) (quic.EarlyConnection, error) {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "Accept", arg0)
	ret0, _ := ret[0].(quic.EarlyConnection)
	ret1, _ := ret[1].(error)
	return ret0, ret1
}

// Accept indicates an expected call of Accept.
func (mr *MockQUICEarlyListenerMockRecorder) Accept(arg0 any) *QUICEarlyListenerAcceptCall {
	mr.mock.ctrl.T.Helper()
	call := mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "Accept", reflect.TypeOf((*MockQUICEarlyListener)(nil).Accept), arg0)
	return &QUICEarlyListenerAcceptCall{Call: call}
}

// QUICEarlyListenerAcceptCall wrap *gomock.Call
type QUICEarlyListenerAcceptCall struct {
	*gomock.Call
}

// Return rewrite *gomock.Call.Return
func (c *QUICEarlyListenerAcceptCall) Return(arg0 quic.EarlyConnection, arg1 error) *QUICEarlyListenerAcceptCall {
	c.Call = c.Call.Return(arg0, arg1)
	return c
}

// Do rewrite *gomock.Call.Do
func (c *QUICEarlyListenerAcceptCall) Do(f func(context.Context) (quic.EarlyConnection, error)) *QUICEarlyListenerAcceptCall {
	c.Call = c.Call.Do(f)
	return c
}

// DoAndReturn rewrite *gomock.Call.DoAndReturn
func (c *QUICEarlyListenerAcceptCall) DoAndReturn(f func(context.Context) (quic.EarlyConnection, error)) *QUICEarlyListenerAcceptCall {
	c.Call = c.Call.DoAndReturn(f)
	return c
}

// Addr mocks base method.
func (m *MockQUICEarlyListener) Addr() net.Addr {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "Addr")
	ret0, _ := ret[0].(net.Addr)
	return ret0
}

// Addr indicates an expected call of Addr.
func (mr *MockQUICEarlyListenerMockRecorder) Addr() *QUICEarlyListenerAddrCall {
	mr.mock.ctrl.T.Helper()
	call := mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "Addr", reflect.TypeOf((*MockQUICEarlyListener)(nil).Addr))
	return &QUICEarlyListenerAddrCall{Call: call}
}

// QUICEarlyListenerAddrCall wrap *gomock.Call
type QUICEarlyListenerAddrCall struct {
	*gomock.Call
}

// Return rewrite *gomock.Call.Return
func (c *QUICEarlyListenerAddrCall) Return(arg0 net.Addr) *QUICEarlyListenerAddrCall {
	c.Call = c.Call.Return(arg0)
	return c
}

// Do rewrite *gomock.Call.Do
func (c *QUICEarlyListenerAddrCall) Do(f func() net.Addr) *QUICEarlyListenerAddrCall {
	c.Call = c.Call.Do(f)
	return c
}

// DoAndReturn rewrite *gomock.Call.DoAndReturn
func (c *QUICEarlyListenerAddrCall) DoAndReturn(f func() net.Addr) *QUICEarlyListenerAddrCall {
	c.Call = c.Call.DoAndReturn(f)
	return c
}

// Close mocks base method.
func (m *MockQUICEarlyListener) Close() error {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "Close")
	ret0, _ := ret[0].(error)
	return ret0
}

// Close indicates an expected call of Close.
func (mr *MockQUICEarlyListenerMockRecorder) Close() *QUICEarlyListenerCloseCall {
	mr.mock.ctrl.T.Helper()
	call := mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "Close", reflect.TypeOf((*MockQUICEarlyListener)(nil).Close))
	return &QUICEarlyListenerCloseCall{Call: call}
}

// QUICEarlyListenerCloseCall wrap *gomock.Call
type QUICEarlyListenerCloseCall struct {
	*gomock.Call
}

// Return rewrite *gomock.Call.Return
func (c *QUICEarlyListenerCloseCall) Return(arg0 error) *QUICEarlyListenerCloseCall {
	c.Call = c.Call.Return(arg0)
	return c
}

// Do rewrite *gomock.Call.Do
func (c *QUICEarlyListenerCloseCall) Do(f func() error) *QUICEarlyListenerCloseCall {
	c.Call = c.Call.Do(f)
	return c
}

// DoAndReturn rewrite *gomock.Call.DoAndReturn
func (c *QUICEarlyListenerCloseCall) DoAndReturn(f func() error) *QUICEarlyListenerCloseCall {
	c.Call = c.Call.DoAndReturn(f)
	return c
}