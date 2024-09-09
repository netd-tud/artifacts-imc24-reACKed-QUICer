package main

import (
	"flag"
	"io"
	"log"
	"os"
	"regexp"
	"slices"
	"strconv"
	"strings"

	"github.com/Jeffail/gabs/v2"
)

var (
	qlog_name_sent     string = "transport:packet_sent"
	qlog_name_received string = "transport:packet_received"
	custom_time_param  string = "cc_max_ack_sent_time"
	custom_newly_acked string = "cc_newly_acked_ack_eliciting"
)

func cond(entry *gabs.Container, field string, value string) bool {
	val, ok := entry.Search(field).Data().(string)
	return ok && (val == value)
}

func cond_name(entry *gabs.Container, name string) bool {
	return cond(entry, "name", name)
}

func cond_name_sent(entry *gabs.Container) bool {
	return cond_name(entry, qlog_name_sent)
}

func cond_name_received(entry *gabs.Container) bool {
	return cond_name(entry, qlog_name_received)
}

func cond_pkn_space(entry *gabs.Container, value string) bool {
	return cond(entry, "data_header_packet_type", value)
}

func cond_initial(entry *gabs.Container) bool {
	return cond_pkn_space(entry, "initial")
}

func cond_handshake(entry *gabs.Container) bool {
	return cond_pkn_space(entry, "handshake")
}

func cond_1RTT(entry *gabs.Container) bool {
	return cond_pkn_space(entry, "1RTT")
}

type PTOInfos struct {
	Time       interface{}
	FrameTypes string
}
type Packets struct {
	Initial   map[uint64]PTOInfos
	Handshake map[uint64]PTOInfos
	OneRTT    map[uint64]PTOInfos
}
type Acked struct {
	Initial   map[uint64]bool
	Handshake map[uint64]bool
	OneRTT    map[uint64]bool
}

func get_ack_range(entry *gabs.Container) (string, bool) {
	val, ok := entry.Search("frame_acked_ranges").Data().(string)
	return val, ok
}

func get_pkn(entry *gabs.Container) (uint64, bool) {
	val := entry.Search("data_header_packet_number").Data()

	switch val.(type) {
	case float64:
		return uint64(val.(float64)), true
	case int64:
		return uint64(val.(int64)), true
	case string:
		i, err := strconv.ParseUint(val.(string), 10, 64)
		if err == nil {
			return i, true
		}
	}

	return val.(uint64), true
}

func get_time(entry *gabs.Container) (interface{}, bool) {
	val, ok := entry.Search("time").Data().(interface{})
	return val, ok
}

func get_frame_types(entry *gabs.Container) (string, bool) {
	val, ok := entry.Search("frame_frame_type").Data().(string)
	return val, ok
}

func strSliceToInt(sa []string) []uint64 {
	ret := make([]uint64, 0, len(sa))
	for _, a := range sa {
		i, err := strconv.ParseUint(a, 10, 64)
		if err != nil {
			// On error continue (accepts null values.)
			continue
		}
		ret = append(ret, i)
	}
	return ret
}

func parse_ack_ranges(ranges string) ([]uint64, map[uint64]bool, uint64) {
	// Usually a string: [1,2,5,6],[8,9], with pairs of ack ranges.
	// reRanges := regexp.MustCompile("\\[([^\\[]*?)]")
	reRanges := regexp.MustCompile(`\[?\[?(\d+,?(\d+)?)]?]?`)
	bracket_ranges := reRanges.FindAllStringSubmatch(ranges, -1)
	int_ranges := []uint64{}
	expanded := map[uint64]bool{}

	for _, r := range bracket_ranges {
		new_range := strSliceToInt(strings.Split(r[1], ","))

		// Extend to pairs if not equal amount
		if len(new_range) == 1 {
			new_range = append(new_range, new_range[len(new_range)-1])
		}

		// Parse in pairs of two and expand
		if len(new_range)%2 != 0 {
			log.Fatal("ACK Range does not contain pairs of ranges")
		}

		int_ranges = append(int_ranges, new_range...)

		for i := 0; i+1 <= len(new_range); i = i + 2 {
			minimum, maximum := int_ranges[i], int_ranges[i+1]
			for it := minimum; it <= maximum; it += 1 {
				expanded[it] = true
			}
		}
	}

	if len(int_ranges) > 0 {
		return int_ranges, expanded, slices.Max(int_ranges)
	}
	return int_ranges, expanded, 0
}

func cond_contains_ack_eliciting_frame(infos PTOInfos) bool {
	// df_sent["data_fi_frame_type"].str.replace("ack,|ack|padding,|padding", "", regex=True).str.len()>0
	frames := strings.ReplaceAll(infos.FrameTypes, "ack", "")
	frames = strings.ReplaceAll(frames, "padding", "")
	frames = strings.ReplaceAll(frames, ",", "")
	return len(frames) > 0
}

func ContainsAckEliciting(candidates map[uint64]bool, sent map[uint64]PTOInfos) bool {
	for key := range candidates {
		if val, ok := sent[key]; ok {
			if cond_contains_ack_eliciting_frame(val) {
				return true
			}
		}
	}
	return false
}

func Difference(acked map[uint64]bool, new_ack_range map[uint64]bool) (map[uint64]bool, map[uint64]bool) {
	n := map[uint64]bool{}

	for key := range new_ack_range {
		if _, ok := acked[key]; !ok {
			n[key] = true
			// Add to acked
			acked[key] = true
		}
	}
	return acked, n
}

func run(in *string, out *string) {
	jsonFile, err := os.Open(*in)
	defer jsonFile.Close()
	if err != nil {
		log.Fatal(err)
	}

	bytes, err := io.ReadAll(jsonFile)
	if err != nil {
		log.Fatal(err)
	}

	jsonData, err := gabs.ParseJSON(bytes)
	if err != nil {
		log.Fatal(err)
	}

	// Create map of packets send and received per namespace
	sent := Packets{
		Initial:   map[uint64]PTOInfos{},
		Handshake: map[uint64]PTOInfos{},
		OneRTT:    map[uint64]PTOInfos{},
	}

	for _, entry := range jsonData.Children() {
		if cond_name_sent(entry) {
			pkn, ok := get_pkn(entry)
			if !ok {
				log.Fatal("Could not extract packet number")
			}
			time, ok := get_time(entry)
			if !ok {
				log.Fatalf("Unable to extract time for PKN %s", pkn)
			}

			types, ok := get_frame_types(entry)
			if !ok {
				log.Fatalf("Unable to extract frame_types for PKN %s", pkn)
			}

			info := PTOInfos{
				Time:       time,
				FrameTypes: types,
			}

			if cond_initial(entry) {
				sent.Initial[pkn] = info
			} else if cond_handshake(entry) {
				sent.Handshake[pkn] = info
			} else if cond_1RTT(entry) {
				sent.OneRTT[pkn] = info
			}
		}
	}

	// Second pass to account for out of order packet reception
	acked_so_far := Acked{
		Initial:   map[uint64]bool{},
		Handshake: map[uint64]bool{},
		OneRTT:    map[uint64]bool{},
	}
	for _, entry := range jsonData.Children() {
		if cond_name_received(entry) {
			ack_range, ok := get_ack_range(entry)
			if !ok {
				log.Fatal("Could not extract ack_range")
			}

			_, expanded_ranges, max_acked := parse_ack_ranges(ack_range)
			// Don't do anything if ack_range is empty
			if len(expanded_ranges) <= 0 {
				continue
			}

			var current map[uint64]bool
			if cond_initial(entry) {
				current = acked_so_far.Initial
			} else if cond_handshake(entry) {
				current = acked_so_far.Handshake
			} else if cond_1RTT(entry) {
				current = acked_so_far.OneRTT
			}

			// Test if ack-eliciting packet contained in ack range
			var newly_acked map[uint64]bool
			_, newly_acked = Difference(current, expanded_ranges)

			// Add current range
			for k, v := range expanded_ranges {
				current[k] = v
			}

			if cond_initial(entry) {
				entry.Set(sent.Initial[max_acked].Time, custom_time_param)
				entry.Set(ContainsAckEliciting(newly_acked, sent.Initial), custom_newly_acked)
			} else if cond_handshake(entry) {
				entry.Set(sent.Handshake[max_acked].Time, custom_time_param)
				entry.Set(ContainsAckEliciting(newly_acked, sent.Handshake), custom_newly_acked)
			} else if cond_1RTT(entry) {
				entry.Set(sent.OneRTT[max_acked].Time, custom_time_param)
				entry.Set(ContainsAckEliciting(newly_acked, sent.OneRTT), custom_newly_acked)
			}
		}
	}

	data := jsonData.String()

	os.WriteFile(*out, []byte(data), 0666)
}

func main() {
	inputFile := flag.String("i", "", "input file")
	outputFile := flag.String("o", "", "output file")
	flag.Parse()

	run(inputFile, outputFile)
}
