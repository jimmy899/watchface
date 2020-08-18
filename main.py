import json
from PIL import Image 

def readWord(content):
        offset = 0
        ret = 0
        # print("readWord")
        while True:
                ret |= (content[offset]&0x7f) << (offset*7)
                if content[offset] & 0x80 == 0:
                        offset = offset + 1
                        break
                offset = offset + 1
        return (ret, offset)
        


def readElement(content):
        flag = content[0] & 7
        rawid = content[0] >> 3
        
        word, skip = readWord(content[1:])
        # print("flag: %d, rawid: %d, word: %d, skip: %d" % (flag, rawid, word, skip))
        if flag & 2 == 2:
                # print("hasChild(%d , %d): %s" % (1+skip, 1+skip+word, content[1+skip:1+skip+word]))
                retList, skip2 = readList(content[1+skip:1+skip+word])
                #print("skip2: %d" % skip2)
                return (rawid, flag, retList, 1+skip+skip2)
        else:
                return (rawid, flag, word, 1+skip)
        
def readList(content):
        ret = []
        offset = 0
        # print("readList")
        """
        while offset < len(content):
                word, skip = readWord(content[offset:])
                if next == 0:
                        # print("error, offset=%d, skip=%d\n" % (offset, skip))
                        break
                # else:
                #        print("offset=%d, skip=%d\n" % (offset, skip))
                # print("word: %d\n" % word)
                ret.append(word)
                offset += skip
        return (ret, offset)
        """
        while offset < len(content):
                rawid, flag, word, skip = readElement(content[offset:])
                # print("readList: flag: %d, rawid: %d, skip: %d" % (flag, rawid, skip))
                # print(word)
                if skip == 0:
                        print("fatal: skip=0")
                        break
                ret.append({"id": rawid, "flag": flag, "value": word})
                offset += skip
        return (ret, offset)
        
        
"""
        STDHDR 40 or 64 (bip)
        
        parameter size: {offset: 36, size: 4, little-endian}

        parameter: {offset: 40, size: parameter size, payload: {element, list0}}
        parameter[0]: parameter table size
        parameter[1]: resources count
        
        parameter table
        {
                list {offset: list0[0], size: list0[1] }
        }
        resource offset table
        {
                count: resources count
                size: 4byte each
                payload: 0-base offset
        }
        resource 
        {
                raw bitmap
        }
        

"""
        
        
r = 0

wf = open("1.bin", 'rb')
if wf is not None:
        

        content = wf.read(16)
        r += len(content)
        if content[0xb] == 0xff:
                print("bip")
                extHdrLen = 40
                unknownOffset = 32
                paramSizeOffset = 36
        else:
                print("non-bip")
                extHdrLen = 64
                unknownOffset = 52
                paramSizeOffset = 56
                
        content += wf.read(extHdrLen - r)
        
        paramSize = int.from_bytes(content[paramSizeOffset:paramSizeOffset+4], 'little')
        unknownSize = int.from_bytes(content[unknownOffset:unknownOffset+4], 'little')
        print("paramSize: %d" % paramSize)
        print("unknownSize: %d" % unknownSize)
        
        content += wf.read(paramSize)
        print("accumated content length: %x" % len(content))
        
        rid, flag, ret, skip = readElement(content[extHdrLen:extHdrLen+paramSize])
        print("rid: %d, flag: %02x, skip: %d" % (rid, flag, skip))
        print(ret)
        
        paramTblLen = ret[0]["value"]
        nrImages = ret[1]["value"]    
        print("paramTblLen: %d, nrImages: %d" % (ret[0]["value"], ret[1]["value"]))
        
        print("%d %d %s" % (extHdrLen+skip, extHdrLen+paramSize, content[extHdrLen+skip:extHdrLen+paramSize]))
        
        ret, skip2 = readList(content[extHdrLen+skip:extHdrLen+paramSize])
        # print("main: skip2: %d" % skip2)
        # print(json.dumps(ret))
        
        content += wf.read(paramTblLen)
        print("accumated content length: %d" % len(content))
        
        parameterTableOffset = extHdrLen+paramSize
        parameterTable = []

        for desc in ret:
                
                print("desc: %d" % desc["id"])
                print("[0]: %d" % desc["value"][0]["value"])
                print("[1]: %d" % desc["value"][1]["value"])
                
                # print("listraw(%d, %d): " % (parameterTableOffset+desc["value"][0]["value"], parameterTableOffset+desc["value"][0]["value"]+desc["value"][1]["value"]),  content[parameterTableOffset+desc["value"][0]["value"]:parameterTableOffset+desc["value"][0]["value"]+desc["value"][1]["value"]])
                parameter = readList(content[parameterTableOffset+desc["value"][0]["value"]:parameterTableOffset+desc["value"][0]["value"]+desc["value"][1]["value"]])
                print("list: ", json.dumps(parameter))
                parameterTable.append({"id": desc["id"], "parameter": parameter})

        resourceOffsetTableOffset = len(content)
        content += wf.read(nrImages * 4)
        resourceOffsets = []
        
        resourceTableOffset = 0 #wf.tell()
        
        for i in range(nrImages):
                of = int.from_bytes(content[resourceOffsetTableOffset+i*4:resourceOffsetTableOffset+i*4+4], 'little')
                # print("of[%d]=%x" % (i, of + resourceTableOffset))
                resourceOffsets.append(of)
                
        for i in range(len(resourceOffsets)-1):
                if True:
                        tmp = wf.read(resourceOffsets[i+1]-resourceOffsets[i])
                        if len(tmp) != resourceOffsets[i+1]-resourceOffsets[i]:
                                print("error: %d %d %d" % (i, len(tmp), resourceOffsets[i+1]))
                                
                        width = int.from_bytes(tmp[4:6], 'little')
                        height = int.from_bytes(tmp[6:8], 'little')
                        stride = int.from_bytes(tmp[8:10], 'little')
                        depth = int.from_bytes(tmp[10:12], 'little')
                        color = int.from_bytes(tmp[12:14], 'little')
                        trans = int.from_bytes(tmp[14:16], 'little')
                        
                        """
                        print("width: %d height: %d stride: %d depth: %d color: %d trans: %d len: %d" % 
                                (width, height, stride, depth, color, trans, len(tmp)))
                        """
                                
                        offset = 16 + color * 4
                        
                        # {r,g,b,a} * stride

                        if depth == 16:
                                # not fixed
                                # im = Image.frombytes('F', (width, height), tmp[offset:], 'raw', "F;16B")
                                
                                im = Image.new(mode = "RGB", size=(width, height))
                                for y in range(height):
                                        for x in range(width):
                                                # print("x: %d y: %d" % (offset+y*stride+x, offset+y*stride+x+depth/8))
                                                pix = int.from_bytes(tmp[offset+y*stride+x*2:offset+y*stride+x*2+int(depth/8)], 'little')
                                                # print("%04x" % pix)
                                                # print("tmp: %02x %02x %02x %02x" % (tmp[offset+y*stride+x], tmp[offset+y*stride+x+1], 0, 0))
                                                im.putpixel((x, y), ((pix >> 11)<<3, ((pix >> 5) & 0x3f)<<2, (pix & 0x1f)<<3))                                
                                
                        else:
                                im = Image.frombytes('RGBA', (width, height), tmp[offset:], 'raw')
                                
                        # im.show()
                        im.save("output/%s.png" % i)
                                
                        # break                        
                        
  
