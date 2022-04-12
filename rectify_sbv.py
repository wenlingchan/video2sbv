import argparse


def _read_sbv(sbv_file):
    sbv_list = []

    with open(sbv_file, "r") as f:
        for l in f:
            line = l.strip()
            if len(line) == 0:
                continue
            elif line[0:2] == "0:":
                sbv_list.append({"time": line, "text": ""})
            else:
                sbv_list[-1]["text"] += line
    
    return sbv_list


def _rectify_sbv(args):
    src_sbv_list = _read_sbv(args["src_sbv_file"])
    ref_sbv_list = _read_sbv(args["ref_sbv_file"])
    assert len(src_sbv_list) == len(ref_sbv_list)
    
    for i in range(len(src_sbv_list)):
        src_sbv_list[i]["text"] = ref_sbv_list[i]["text"]
    
    with open(args["dst_sbv_file"], "w") as f:
        for item in src_sbv_list:
            f.write(item["time"])
            f.write("\n")
            f.write(item["text"])
            f.write("\n\n")
    
    print("Done.")


def _get_parser():
    parser = argparse.ArgumentParser(description="Rectify SBV file with reference")
    parser.add_argument("src_sbv_file", help="Source SBV file path")
    parser.add_argument("ref_sbv_file", help="Reference SBV file path")
    parser.add_argument("dst_sbv_file", help="Destination SBV file path")
    return parser


if __name__ == "__main__":
    parser = _get_parser()
    args = vars(parser.parse_args())
    
    _rectify_sbv(args)