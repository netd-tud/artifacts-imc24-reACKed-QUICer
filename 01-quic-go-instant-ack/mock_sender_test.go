// Code generated by MockGen. DO NOT EDIT.
// Source: github.com/quic-go/quic-go (interfaces: Sender)
//
// Generated by this command:
//
//	mockgen -typed -build_flags=-tags=gomock -package quic -self_package github.com/quic-go/quic-go -destination mock_sender_test.go github.com/quic-go/quic-go Sender
//
// Package quic is a generated GoMock package.
package quic

import (
	reflect "reflect"

	protocol "github.com/quic-go/quic-go/internal/protocol"
	gomock "go.uber.org/mock/gomock"
)

// MockSender is a mock of Sender interface.
type MockSender struct {
	ctrl     *gomock.Controller
	recorder *MockSenderMockRecorder
}

// MockSenderMockRecorder is the mock recorder for MockSender.
type MockSenderMockRecorder struct {
	mock *MockSender
}

// NewMockSender creates a new mock instance.
func NewMockSender(ctrl *gomock.Controller) *MockSender {
	mock := &MockSender{ctrl: ctrl}
	mock.recorder = &MockSenderMockRecorder{mock}
	return mock
}

// EXPECT returns an object that allows the caller to indicate expected use.
func (m *MockSender) EXPECT() *MockSenderMockRecorder {
	return m.recorder
}

// Available mocks base method.
func (m *MockSender) Available() <-chan struct{} {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "Available")
	ret0, _ := ret[0].(<-chan struct{})
	return ret0
}

// Available indicates an expected call of Available.
func (mr *MockSenderMockRecorder) Available() *SenderAvailableCall {
	mr.mock.ctrl.T.Helper()
	call := mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "Available", reflect.TypeOf((*MockSender)(nil).Available))
	return &SenderAvailableCall{Call: call}
}

// SenderAvailableCall wrap *gomock.Call
type SenderAvailableCall struct {
	*gomock.Call
}

// Return rewrite *gomock.Call.Return
func (c *SenderAvailableCall) Return(arg0 <-chan struct{}) *SenderAvailableCall {
	c.Call = c.Call.Return(arg0)
	return c
}

// Do rewrite *gomock.Call.Do
func (c *SenderAvailableCall) Do(f func() <-chan struct{}) *SenderAvailableCall {
	c.Call = c.Call.Do(f)
	return c
}

// DoAndReturn rewrite *gomock.Call.DoAndReturn
func (c *SenderAvailableCall) DoAndReturn(f func() <-chan struct{}) *SenderAvailableCall {
	c.Call = c.Call.DoAndReturn(f)
	return c
}

// Close mocks base method.
func (m *MockSender) Close() {
	m.ctrl.T.Helper()
	m.ctrl.Call(m, "Close")
}

// Close indicates an expected call of Close.
func (mr *MockSenderMockRecorder) Close() *SenderCloseCall {
	mr.mock.ctrl.T.Helper()
	call := mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "Close", reflect.TypeOf((*MockSender)(nil).Close))
	return &SenderCloseCall{Call: call}
}

// SenderCloseCall wrap *gomock.Call
type SenderCloseCall struct {
	*gomock.Call
}

// Return rewrite *gomock.Call.Return
func (c *SenderCloseCall) Return() *SenderCloseCall {
	c.Call = c.Call.Return()
	return c
}

// Do rewrite *gomock.Call.Do
func (c *SenderCloseCall) Do(f func()) *SenderCloseCall {
	c.Call = c.Call.Do(f)
	return c
}

// DoAndReturn rewrite *gomock.Call.DoAndReturn
func (c *SenderCloseCall) DoAndReturn(f func()) *SenderCloseCall {
	c.Call = c.Call.DoAndReturn(f)
	return c
}

// Run mocks base method.
func (m *MockSender) Run() error {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "Run")
	ret0, _ := ret[0].(error)
	return ret0
}

// Run indicates an expected call of Run.
func (mr *MockSenderMockRecorder) Run() *SenderRunCall {
	mr.mock.ctrl.T.Helper()
	call := mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "Run", reflect.TypeOf((*MockSender)(nil).Run))
	return &SenderRunCall{Call: call}
}

// SenderRunCall wrap *gomock.Call
type SenderRunCall struct {
	*gomock.Call
}

// Return rewrite *gomock.Call.Return
func (c *SenderRunCall) Return(arg0 error) *SenderRunCall {
	c.Call = c.Call.Return(arg0)
	return c
}

// Do rewrite *gomock.Call.Do
func (c *SenderRunCall) Do(f func() error) *SenderRunCall {
	c.Call = c.Call.Do(f)
	return c
}

// DoAndReturn rewrite *gomock.Call.DoAndReturn
func (c *SenderRunCall) DoAndReturn(f func() error) *SenderRunCall {
	c.Call = c.Call.DoAndReturn(f)
	return c
}

// Send mocks base method.
func (m *MockSender) Send(arg0 *packetBuffer, arg1 uint16, arg2 protocol.ECN) {
	m.ctrl.T.Helper()
	m.ctrl.Call(m, "Send", arg0, arg1, arg2)
}

// Send indicates an expected call of Send.
func (mr *MockSenderMockRecorder) Send(arg0, arg1, arg2 any) *SenderSendCall {
	mr.mock.ctrl.T.Helper()
	call := mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "Send", reflect.TypeOf((*MockSender)(nil).Send), arg0, arg1, arg2)
	return &SenderSendCall{Call: call}
}

// SenderSendCall wrap *gomock.Call
type SenderSendCall struct {
	*gomock.Call
}

// Return rewrite *gomock.Call.Return
func (c *SenderSendCall) Return() *SenderSendCall {
	c.Call = c.Call.Return()
	return c
}

// Do rewrite *gomock.Call.Do
func (c *SenderSendCall) Do(f func(*packetBuffer, uint16, protocol.ECN)) *SenderSendCall {
	c.Call = c.Call.Do(f)
	return c
}

// DoAndReturn rewrite *gomock.Call.DoAndReturn
func (c *SenderSendCall) DoAndReturn(f func(*packetBuffer, uint16, protocol.ECN)) *SenderSendCall {
	c.Call = c.Call.DoAndReturn(f)
	return c
}

// WouldBlock mocks base method.
func (m *MockSender) WouldBlock() bool {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "WouldBlock")
	ret0, _ := ret[0].(bool)
	return ret0
}

// WouldBlock indicates an expected call of WouldBlock.
func (mr *MockSenderMockRecorder) WouldBlock() *SenderWouldBlockCall {
	mr.mock.ctrl.T.Helper()
	call := mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "WouldBlock", reflect.TypeOf((*MockSender)(nil).WouldBlock))
	return &SenderWouldBlockCall{Call: call}
}

// SenderWouldBlockCall wrap *gomock.Call
type SenderWouldBlockCall struct {
	*gomock.Call
}

// Return rewrite *gomock.Call.Return
func (c *SenderWouldBlockCall) Return(arg0 bool) *SenderWouldBlockCall {
	c.Call = c.Call.Return(arg0)
	return c
}

// Do rewrite *gomock.Call.Do
func (c *SenderWouldBlockCall) Do(f func() bool) *SenderWouldBlockCall {
	c.Call = c.Call.Do(f)
	return c
}

// DoAndReturn rewrite *gomock.Call.DoAndReturn
func (c *SenderWouldBlockCall) DoAndReturn(f func() bool) *SenderWouldBlockCall {
	c.Call = c.Call.DoAndReturn(f)
	return c
}