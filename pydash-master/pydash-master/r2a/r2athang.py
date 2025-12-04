import time
from r2a.ir2a import IR2A
from player.parser import *

class R2AThang(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.qi = [] 
        self.smoothed_throughput = 0 
        self.delta = 0.5 
        self.safety_margin = 0.1 
        self.start_time = 0 

    def initialize(self):
        # Inicialização do algoritmo
        pass

    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()
        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        # 1. Cálculo da meta de bitrate (Eq. 6 do artigo Thang)
        target_bitrate = self.smoothed_throughput * (1 - self.safety_margin)
        
        # Seleção inicial (menor qualidade)
        if not self.qi:
             selected_quality = 0
        else:
             selected_quality = self.qi[0] 
        
        # Seleção baseada na vazão suavizada
        if self.smoothed_throughput > 0:
            for quality in self.qi:
                if quality <= target_bitrate:
                    selected_quality = quality
                else:
                    break
        
        # Inicia cronômetro para medir o próximo download
        self.start_time = time.time()
        
        msg.add_quality_id(selected_quality)
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        # 2. Para cronômetro e calcula vazão real
        end_time = time.time()
        download_time = end_time - self.start_time
        segment_size = msg.get_bit_length()
        
        if download_time <= 0:
            download_time = 0.001 

        instant_throughput = segment_size / download_time

        # Atualiza a média suavizada (Eq. 3 do artigo Thang)
        if self.smoothed_throughput == 0:
            self.smoothed_throughput = instant_throughput
        else:
            self.smoothed_throughput = (1 - self.delta) * self.smoothed_throughput + self.delta * instant_throughput

        self.send_up(msg)

    def finalization(self):
        print("Fim da execução.")